"""
Modèles SQLAlchemy pour la base de données PostgreSQL

Ce fichier définit les tables de la base de données sous forme de classes Python.
Chaque classe représente une table, chaque attribut représente une colonne.
"""

from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, TIMESTAMP, Text, CheckConstraint
from sqlalchemy.sql import func
from .db_connector import Base

class PredictionFeedback(Base):
    """
    Modèle pour stocker les prédictions avec feedback utilisateur
    
    Table : predictions_feedback
    
    Cette table enregistre :
    - Les métriques de performance (temps d'inférence, succès)
    - Les résultats de prédiction (cat/dog, probabilités)
    - Les données utilisateur si consentement RGPD (nom fichier, feedback, commentaire)
    """
    
    __tablename__ = 'predictions_feedback'
    
    # === Colonnes principales ===
    id = Column(Integer, primary_key=True, autoincrement=True)  # Identifiant unique
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())  # Date de création de l'enregistrement
    inference_time_ms = Column(Integer, nullable=False)  # Temps d'inférence en millisecondes
    success = Column(Boolean, nullable=False)  # True si prédiction réussie, False si erreur
    
    # === Résultats de prédiction ===
    prediction_result = Column(String(10), nullable=False)  # 'cat' ou 'dog' (ou 'error' en cas d'échec)
    proba_cat = Column(DECIMAL(5, 2), nullable=False)  # Probabilité chat (0.00 à 100.00)
    proba_dog = Column(DECIMAL(5, 2), nullable=False)  # Probabilité chien (0.00 à 100.00)
    
    # === Données RGPD et feedback utilisateur ===
    rgpd_consent = Column(Boolean, nullable=False, default=False)  # Consentement RGPD de l'utilisateur
    filename = Column(String(255), nullable=True)  # Nom du fichier (NULL si pas de consentement)
    user_feedback = Column(Integer, nullable=True)  # Satisfaction : 1=satisfait, 0=pas satisfait, NULL=non renseigné
    user_comment = Column(Text, nullable=True)  # Commentaire libre de l'utilisateur
    
    # === Contraintes de validation ===
    # CheckConstraint permet de valider les données au niveau de la base de données
    __table_args__ = (
        # Le résultat doit être 'cat', 'dog' ou 'error'
        CheckConstraint("prediction_result IN ('cat', 'dog', 'error')", name='check_prediction_result'),
        
        # Les probabilités doivent être entre 0 et 100
        CheckConstraint('proba_cat >= 0 AND proba_cat <= 100', name='check_proba_cat'),
        CheckConstraint('proba_dog >= 0 AND proba_dog <= 100', name='check_proba_dog'),
        
        # Le feedback utilisateur doit être 0, 1 ou NULL
        CheckConstraint('user_feedback IS NULL OR user_feedback IN (0, 1)', name='check_user_feedback'),
    )
    
    def __repr__(self):
        """
        Représentation textuelle de l'objet (utile pour le débogage)
        Exemple : <PredictionFeedback(id=1, result=cat, rgpd=True)>
        """
        return f"<PredictionFeedback(id={self.id}, result={self.prediction_result}, rgpd={self.rgpd_consent})>"