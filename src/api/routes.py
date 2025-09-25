from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import sys
from pathlib import Path
import time

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from .auth import verify_token
from src.models.predictor import CatDogPredictor

# Imports pour la base de données
from src.database.db_connector import get_db
from src.database.feedback_service import FeedbackService

# Imports pour le monitoring
from src.monitoring.dashboard_service import DashboardService

# Configuration des templates
TEMPLATES_DIR = ROOT_DIR / "src" / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()

# Initialisation du prédicteur
predictor = CatDogPredictor()

@router.get("/", response_class=HTMLResponse, tags=["🌐 Page Web"])
async def welcome(request: Request):
    """Page d'accueil avec interface web qui présente les principales fonctionnalités de l'application"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "model_loaded": predictor.is_loaded()
    })

@router.get("/info", response_class=HTMLResponse, tags=["🌐 Page Web"])
async def info_page(request: Request):
    """Page d'informations"""
    model_info = {
        "name": "Cats vs Dogs Classifier",
        "version": "1.0.0",
        "description": "Modèle CNN pour classification chats/chiens",
        "parameters": predictor.model.count_params() if predictor.is_loaded() else 0,
        "classes": ["Cat", "Dog"],
        "input_size": f"{predictor.image_size[0]}x{predictor.image_size[1]}",
        "model_loaded": predictor.is_loaded()
    }
    return templates.TemplateResponse("info.html", {
        "request": request, 
        "model_info": model_info
    })

@router.get("/inference", response_class=HTMLResponse, tags=["🧠 Inférence"])
async def inference_page(request: Request):
    """Page d'inférence"""
    return templates.TemplateResponse("inference.html", {
        "request": request,
        "model_loaded": predictor.is_loaded()
    })

@router.post("/api/predict", tags=["🧠 Inférence"])
async def predict_api(
    file: UploadFile = File(...),
    rgpd_consent: bool = Form(False),
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    API de prédiction avec enregistrement en base de données
    
    Args:
        file: Image uploadée
        rgpd_consent: Consentement RGPD pour stocker les données personnelles
        token: Token d'authentification
        db: Session de base de données
    """
    if not predictor.is_loaded():
        raise HTTPException(status_code=503, detail="Modèle non disponible")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Format d'image invalide")
    
    # Mesure du temps de début
    start_time = time.perf_counter()
    
    try:
        # Lecture de l'image
        image_data = await file.read()
        
        # Prédiction
        result = predictor.predict(image_data)
        
        # Calcul du temps d'inférence en millisecondes
        end_time = time.perf_counter()
        inference_time_ms = int((end_time - start_time) * 1000)
        
        # Extraction des probabilités
        proba_cat = result['probabilities']['cat'] * 100  # Conversion en pourcentage
        proba_dog = result['probabilities']['dog'] * 100
        
        # Enregistrement en base de données
        feedback_record = FeedbackService.save_prediction_feedback(
            db=db,
            inference_time_ms=inference_time_ms,
            success=True,
            prediction_result=result["prediction"].lower(),  # 'cat' ou 'dog'
            proba_cat=proba_cat,
            proba_dog=proba_dog,
            rgpd_consent=rgpd_consent,
            filename=file.filename if rgpd_consent else None,
            user_feedback=None,  # Sera mis à jour plus tard
            user_comment=None    # Sera mis à jour plus tard
        )
        
        # Préparation de la réponse
        response_data = {
            "filename": file.filename,
            "prediction": result["prediction"],
            "confidence": f"{result['confidence']:.2%}",
            "probabilities": {
                "cat": f"{result['probabilities']['cat']:.2%}",
                "dog": f"{result['probabilities']['dog']:.2%}"
            },
            "inference_time_ms": inference_time_ms,
            "feedback_id": feedback_record.id  # ID pour les mises à jour ultérieures
        }
        
        return response_data
        
    except Exception as e:
        # En cas d'erreur, enregistrer quand même
        end_time = time.perf_counter()
        inference_time_ms = int((end_time - start_time) * 1000)
        
        # Enregistrement de l'erreur en base
        try:
            FeedbackService.save_prediction_feedback(
                db=db,
                inference_time_ms=inference_time_ms,
                success=False,
                prediction_result="error",
                proba_cat=0.0,
                proba_dog=0.0,
                rgpd_consent=False,
                filename=None,
                user_feedback=None,
                user_comment=str(e)
            )
        except:
            pass  # Si l'enregistrement échoue, on continue quand même
        
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction: {str(e)}")

@router.post("/api/update-feedback", tags=["📊 Monitoring"])
async def update_feedback(
    feedback_id: int = Form(...),
    user_feedback: int = Form(None),
    user_comment: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Mise à jour du feedback utilisateur (satisfaction et commentaire)
    
    Args:
        feedback_id: ID de l'enregistrement à mettre à jour
        user_feedback: Satisfaction utilisateur (0 ou 1)
        user_comment: Commentaire optionnel
        db: Session de base de données
    """
    try:
        from src.database.models import PredictionFeedback
        
        # Récupération de l'enregistrement
        record = db.query(PredictionFeedback).filter(
            PredictionFeedback.id == feedback_id
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=404,
                detail="Enregistrement de feedback non trouvé"
            )
        
        # Mise à jour uniquement si RGPD accepté
        if not record.rgpd_consent:
            raise HTTPException(
                status_code=403,
                detail="Consentement RGPD non accepté. Impossible de stocker le feedback."
            )
        
        # Mise à jour des champs
        if user_feedback is not None:
            if user_feedback not in [0, 1]:
                raise HTTPException(
                    status_code=400,
                    detail="user_feedback doit être 0 ou 1"
                )
            record.user_feedback = user_feedback
        
        if user_comment:
            record.user_comment = user_comment
        
        # Sauvegarde en base
        db.commit()
        
        return {
            "success": True,
            "message": "Feedback mis à jour avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )

@router.get("/api/statistics", tags=["📊 Monitoring"])
async def get_statistics(db: Session = Depends(get_db)):
    """
    Récupération des statistiques de prédiction
    
    Returns:
        Statistiques globales sur les prédictions
    """
    try:
        stats = FeedbackService.get_statistics(db)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )

@router.get("/api/recent-predictions", tags=["📊 Monitoring"])
async def get_recent_predictions(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Récupération des prédictions récentes
    
    Args:
        limit: Nombre de prédictions à récupérer (défaut: 10)
    """
    try:
        predictions = FeedbackService.get_recent_predictions(db, limit=limit)
        
        # Formatage des résultats
        results = []
        for pred in predictions:
            results.append({
                "id": pred.id,
                "timestamp": pred.timestamp.isoformat() if pred.timestamp else None,
                "prediction_result": pred.prediction_result,
                "proba_cat": float(pred.proba_cat),
                "proba_dog": float(pred.proba_dog),
                "inference_time_ms": pred.inference_time_ms,
                "success": pred.success,
                "rgpd_consent": pred.rgpd_consent,
                "user_feedback": pred.user_feedback,
                "filename": pred.filename if pred.rgpd_consent else None
            })
        
        return {"predictions": results, "count": len(results)}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des prédictions: {str(e)}"
        )

@router.get("/api/info", tags=["🧠 Inférence"])
async def api_info():
    """Informations API JSON"""
    return {
        "model_loaded": predictor.is_loaded(),
        "model_path": str(predictor.model_path),
        "version": "2.0.0",  # Version mise à jour
        "parameters": predictor.model.count_params() if predictor.is_loaded() else 0,
        "features": [
            "Image classification (cats/dogs)",
            "RGPD compliance",
            "User feedback collection",
            "PostgreSQL monitoring"
        ]
    }

@router.get("/monitoring", response_class=HTMLResponse, tags=["📊 monitoring"])
async def monitoring_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    📊 Dashboard de monitoring
    
    Affiche les métriques et graphiques de surveillance :
    - KPI temps d'inférence moyen
    - Courbe temporelle des temps d'inférence
    - KPI taux de satisfaction
    - Scatter plot de la satisfaction utilisateur
    """
    try:
        # Récupération des données du dashboard
        dashboard_data = DashboardService.get_dashboard_data(db)
        
        return templates.TemplateResponse("monitoring.html", {
            "request": request,
            **dashboard_data
        })
    except Exception as e:
        return templates.TemplateResponse("monitoring.html", {
            "request": request,
            "error": f"Erreur lors du chargement des données : {str(e)}"
        })


@router.get("/health", tags=["💚 Santé système"])
async def health_check(db: Session = Depends(get_db)):
    """Vérification de l'état de l'API et de la base de données"""
    db_status = "connected"
    try:
        # Test de connexion à la base de données
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "model_loaded": predictor.is_loaded(),
        "database": db_status
    }