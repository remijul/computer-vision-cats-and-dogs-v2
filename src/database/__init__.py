"""
Package de gestion de la base de données PostgreSQL

Ce fichier __init__.py permet de :
1. Simplifier les imports : from src.database import get_db, FeedbackService
   au lieu de from src.database.db_connector import get_db
2. Documenter l'API publique du package via __all__
3. Contrôler ce qui est accessible depuis l'extérieur
4. Améliorer l'auto-complétion des IDE
"""

from .db_connector import Base, engine, get_db, get_db_session
from .models import PredictionFeedback
from .feedback_service import FeedbackService

# Liste des symboles exportés publiquement
# Permet de contrôler ce qui est importé avec "from src.database import *"
__all__ = [
    # Connexion et session
    'Base',              # Base SQLAlchemy pour les modèles
    'engine',            # Moteur de connexion PostgreSQL
    'get_db',            # Dépendance FastAPI pour obtenir une session
    'get_db_session',    # Fonction pour obtenir une session directement
    
    # Modèles
    'PredictionFeedback',  # Modèle de la table predictions_feedback
    
    # Services
    'FeedbackService'    # Service métier pour gérer les feedbacks
]

__version__ = '2.0.0'