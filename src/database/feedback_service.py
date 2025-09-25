from datetime import datetime
from sqlalchemy.orm import Session
from .models import PredictionFeedback # Import relatif ici car l'appel se fait à l'intérieur du module 

class FeedbackService:
    """Service pour gérer les enregistrements de feedback"""
    
    @staticmethod
    def save_prediction_feedback(
        db: Session,
        inference_time_ms: int,
        success: bool,
        prediction_result: str,
        proba_cat: float,
        proba_dog: float,
        rgpd_consent: bool,
        filename: str = None,
        user_feedback: int = None,
        user_comment: str = None
    ) -> PredictionFeedback:
        """
        Enregistre une prédiction avec feedback dans la base de données
        
        Args:
            db: Session SQLAlchemy
            inference_time_ms: Temps d'inférence en millisecondes
            success: Succès de la prédiction
            prediction_result: Résultat ('cat' ou 'dog')
            proba_cat: Probabilité classe chat (0-100)
            proba_dog: Probabilité classe chien (0-100)
            rgpd_consent: Consentement RGPD
            filename: Nom du fichier (si RGPD OK)
            user_feedback: Satisfaction utilisateur 0/1 (si RGPD OK)
            user_comment: Commentaire utilisateur (si RGPD OK)
        
        Returns:
            PredictionFeedback: Objet créé
        """
        # Si pas de consentement RGPD, on ne stocke pas les données personnelles
        if not rgpd_consent:
            filename = None
            user_feedback = None
            user_comment = None
        
        # Création de l'enregistrement
        feedback = PredictionFeedback(
            inference_time_ms=inference_time_ms,
            success=success,
            prediction_result=prediction_result,
            proba_cat=round(proba_cat, 2),
            proba_dog=round(proba_dog, 2),
            rgpd_consent=rgpd_consent,
            filename=filename,
            user_feedback=user_feedback,
            user_comment=user_comment
        )
        
        # Enregistrement en base
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        return feedback
    
    @staticmethod
    def get_recent_predictions(db: Session, limit: int = 10):
        """Récupère les dernières prédictions"""
        return db.query(PredictionFeedback)\
            .order_by(PredictionFeedback.timestamp.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_statistics(db: Session):
        """Calcule des statistiques sur les prédictions"""
        from sqlalchemy import func
        
        total = db.query(func.count(PredictionFeedback.id)).scalar()
        success_count = db.query(func.count(PredictionFeedback.id)).filter(PredictionFeedback.success == True).scalar()
        rgpd_consent_count = db.query(func.count(PredictionFeedback.id)).filter(PredictionFeedback.rgpd_consent == True).scalar()
        
        return {
            'total_predictions': total or 0,
            'successful_predictions': success_count or 0,
            'rgpd_consents': rgpd_consent_count or 0,
            'success_rate': round((success_count / total * 100) if total > 0 else 0, 2)
        }