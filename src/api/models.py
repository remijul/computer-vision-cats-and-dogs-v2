from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PredictionRequest(BaseModel):
    """Modèle pour la requête de prédiction"""
    rgpd_consent: bool = Field(default=False, description="Consentement RGPD pour stocker les données")
    filename: Optional[str] = Field(default=None, description="Nom du fichier image")

class FeedbackRequest(BaseModel):
    """Modèle pour le feedback utilisateur"""
    prediction_id: int = Field(description="ID de la prédiction concernée")
    user_feedback: Optional[int] = Field(default=None, ge=0, le=1, description="Satisfaction: 0=pas satisfait, 1=satisfait")
    user_comment: Optional[str] = Field(default=None, max_length=500, description="Commentaire utilisateur")

class PredictionResponse(BaseModel):
    """Modèle pour la réponse de prédiction"""
    prediction_id: int
    prediction_result: str
    proba_cat: float
    proba_dog: float
    inference_time_ms: int
    success: bool
    timestamp: datetime

class FeedbackResponse(BaseModel):
    """Modèle pour la réponse de feedback"""
    message: str
    feedback_recorded: bool