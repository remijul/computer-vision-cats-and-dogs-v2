#!/usr/bin/env python3
"""Test pytest simple sur la route /health"""

import pytest
import requests
import sys
from pathlib import Path

# Configuration
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import API_CONFIG

# Configuration des tests
BASE_URL = f"http://{API_CONFIG["host"]}:{API_CONFIG["port"]}"

def test_quick_api_health():
    """Test très rapide de santé de l'API"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        print(f"\nStatut API: {data.get('status', 'unknown')}")
        print(f"Modèle chargé: {data.get('model_loaded', False)}")
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"API non accessible: {e}")

# Permet l'exécution directe du fichier
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])