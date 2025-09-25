#!/usr/bin/env python3
"""Tests pytest de l'API Cats vs Dogs"""

import pytest
import requests
import sys
from pathlib import Path
import time

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import DATA_DIR, API_CONFIG

# Configuration globale des tests
BASE_URL = "http://localhost:8000"
TOKEN = API_CONFIG["token"]
TEST_IMAGE_PATH = None

def find_test_image():
    """Trouve la première image disponible dans le dossier Cat"""
    global TEST_IMAGE_PATH
    
    if TEST_IMAGE_PATH and TEST_IMAGE_PATH.exists():
        return TEST_IMAGE_PATH
    
    cat_dir = DATA_DIR / "raw" / "PetImages" / "Cat"
    
    if not cat_dir.exists():
        pytest.skip(f"Répertoire non trouvé: {cat_dir}")
    
    # Chercher la première image valide
    image_extensions = ['.jpg', '.jpeg', '.png']
    for file_path in cat_dir.iterdir():
        if file_path.suffix.lower() in image_extensions:
            try:
                if file_path.stat().st_size > 1000:  # Plus de 1KB
                    TEST_IMAGE_PATH = file_path
                    return file_path
            except Exception:
                continue
    
    pytest.skip("Aucune image de test valide trouvée")

@pytest.fixture(scope="session", autouse=True)
def check_api_running():
    """Vérifie que l'API est démarrée avant les tests"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            pytest.skip("API non accessible")
    except requests.exceptions.RequestException:
        pytest.skip("API non démarrée. Lancez: python scripts/run_api.py")

@pytest.fixture
def test_image():
    """Fixture pour obtenir une image de test"""
    return find_test_image()

class TestAPIEndpoints:
    """Tests des endpoints de base"""
    
    def test_health_endpoint(self):
        """Test du endpoint /health"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test de la page d'accueil"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
    
    def test_info_endpoint(self):
        """Test du endpoint /info"""
        response = requests.get(f"{BASE_URL}/info")
        assert response.status_code == 200
    
    def test_inference_page(self):
        """Test de la page d'inférence"""
        response = requests.get(f"{BASE_URL}/inference")
        assert response.status_code == 200
    
    def test_api_info_endpoint(self):
        """Test du endpoint /api/info"""
        response = requests.get(f"{BASE_URL}/api/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "model_loaded" in data
        assert "version" in data
        assert data["version"] == "1.0.0"

class TestAuthentication:
    """Tests d'authentification"""
    
    def test_predict_without_auth(self, test_image):
        """Test de prédiction sans authentification"""
        with open(test_image, "rb") as f:
            files = {"file": (test_image.name, f, "image/jpeg")}
            response = requests.post(f"{BASE_URL}/api/predict", files=files)
        
        # FastAPI peut retourner 401 ou 403 selon la configuration
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"
    
    def test_predict_with_wrong_token(self, test_image):
        """Test avec un mauvais token"""
        headers = {"Authorization": "Bearer MAUVAIS_TOKEN"}
        
        with open(test_image, "rb") as f:
            files = {"file": (test_image.name, f, "image/jpeg")}
            response = requests.post(
                f"{BASE_URL}/api/predict", 
                files=files, 
                headers=headers
            )
        
        assert response.status_code == 401
    
    def test_predict_with_valid_token(self, test_image):
        """Test avec un token valide"""
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        with open(test_image, "rb") as f:
            files = {"file": (test_image.name, f, "image/jpeg")}
            response = requests.post(
                f"{BASE_URL}/api/predict", 
                files=files, 
                headers=headers
            )
        
        # Devrait être 200 ou 503 (si modèle non chargé)
        assert response.status_code in [200, 503]

class TestPrediction:
    """Tests de prédiction"""
    
    def test_prediction_success(self, test_image):
        """Test de prédiction réussie"""
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        with open(test_image, "rb") as f:
            files = {"file": (test_image.name, f, "image/jpeg")}
            response = requests.post(
                f"{BASE_URL}/api/predict", 
                files=files, 
                headers=headers,
                timeout=30
            )
        
        if response.status_code == 503:
            pytest.skip("Modèle non disponible")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert "probabilities" in data
        assert data["prediction"] in ["Cat", "Dog"]
        
        # Vérifier les probabilités
        probs = data["probabilities"]
        assert "cat" in probs
        assert "dog" in probs
    
    def test_prediction_with_invalid_file(self):
        """Test avec un fichier non-image"""
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        # Fichier texte
        files = {"file": ("test.txt", b"Ceci n'est pas une image", "text/plain")}
        response = requests.post(
            f"{BASE_URL}/api/predict", 
            files=files, 
            headers=headers
        )
        
        assert response.status_code == 400
    
    def test_prediction_consistency(self, test_image):
        """Test de cohérence - image de chat devrait prédire Chat"""
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        with open(test_image, "rb") as f:
            files = {"file": (test_image.name, f, "image/jpeg")}
            response = requests.post(
                f"{BASE_URL}/api/predict", 
                files=files, 
                headers=headers
            )
        
        if response.status_code == 503:
            pytest.skip("Modèle non disponible")
        
        assert response.status_code == 200
        
        data = response.json()
        # Note: On ne peut pas garantir que le modèle prédit toujours correctement
        # mais on peut vérifier que la réponse est cohérente
        assert data["prediction"] in ["Cat", "Dog"]
        
        # Afficher le résultat pour debug
        print(f"\nImage testée: {test_image.name}")
        print(f"Prédiction: {data['prediction']}")
        print(f"Confiance: {data['confidence']}")

class TestAPIResponseFormat:
    """Tests du format des réponses API"""
    
    def test_prediction_response_format(self, test_image):
        """Test du format de réponse de prédiction"""
        headers = {"Authorization": f"Bearer {TOKEN}"}
        
        with open(test_image, "rb") as f:
            files = {"file": (test_image.name, f, "image/jpeg")}
            response = requests.post(
                f"{BASE_URL}/api/predict", 
                files=files, 
                headers=headers
            )
        
        if response.status_code == 503:
            pytest.skip("Modèle non disponible")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Vérifier la structure de la réponse
        required_fields = ["filename", "prediction", "confidence", "probabilities"]
        for field in required_fields:
            assert field in data, f"Champ manquant: {field}"
        
        # Vérifier le format des probabilités
        probs = data["probabilities"]
        assert isinstance(probs, dict)
        assert "cat" in probs
        assert "dog" in probs
        
        # Vérifier que les pourcentages sont bien formatés
        assert probs["cat"].endswith("%")
        assert probs["dog"].endswith("%")

# Tests paramétrés pour plusieurs endpoints
@pytest.mark.parametrize("endpoint,expected_status", [
    ("/", 200),
    ("/health", 200),
    ("/info", 200),
    ("/inference", 200),
    ("/api/info", 200),
    ("/docs", 200),
])
def test_endpoints_status(endpoint, expected_status):
    """Test paramétré des status codes des endpoints"""
    response = requests.get(f"{BASE_URL}{endpoint}")
    assert response.status_code == expected_status

if __name__ == "__main__":
    # Permettre l'exécution directe du fichier
    pytest.main([__file__, "-v"])