from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from .routes import router

app = FastAPI(
    title="🐱🐶 Cats vs Dogs Classifier",
    description="""
**API complète de Computer Vision avec monitoring intégré pour classifier des images de chats et de chiens**

## 🎯 Fonctionnalités

**🧠 Modèle d'IA**
* Architecture : CNN (Convolutional Neural Network)
* Framework : Keras × TensorFlow
* Classes : Chat 🐱 | Chien 🐶

**🔬 Testez le modèle**
* Uploadez vos propres images
* Obtenez les probabilités de prédiction
* Temps d'inférence en temps réel

**📊 Monitoring & Analytics**
* Enregistrement des prédictions en PostgreSQL
* Collecte de feedback utilisateur (avec consentement RGPD)
* Statistiques d'utilisation et de performance

## 🔐 Authentification

L'API utilise un **Bearer Token** pour sécuriser les endpoints d'inférence.

Format : `Authorization: Bearer <votre_token>`

## 📈 Endpoints principaux

**Routes Web**
* `/` - Interface web principale
* `/inference` - Page de test du modèle
* `/info` - Informations sur le modèle

**Routes API**
* `POST /api/predict` - Endpoint de prédiction
* `GET /api/statistics` - Statistiques du monitoring
* `GET /api/recent-predictions` - Dernières prédictions
* `POST /api/update-feedback` - Mise à jour du feedback
* `GET /health` - État de santé de l'API

## 🛡️ RGPD

Le système respecte le RGPD :
* ✅ Consentement explicite de l'utilisateur
* ✅ Données personnelles stockées uniquement avec accord
* ✅ Métriques anonymes par défaut

## 📚 Documentation

* **Swagger UI** : `/docs` (cette page)
* **ReDoc** : `/redoc` (documentation alternative)
* **OpenAPI JSON** : `/openapi.json`

**Version** : 2.0.0 | **License** : MIT
    """,
    version="2.0.0",
    contact={
        "name": "Rémi Julien",
        "url": "https://github.com/remijul/computer-vision-cats-and-dogs",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Ajouter les routes
app.include_router(router)

# Optionnel : servir des fichiers statiques
STATIC_DIR = ROOT_DIR / "src" / "web" / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")