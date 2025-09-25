"""
Service pour générer les métriques et graphiques du dashboard de monitoring

Ce service récupère les données de PostgreSQL et génère :
- KPI du temps d'inférence moyen
- Courbe temporelle des temps d'inférence
- KPI du taux de satisfaction utilisateur
- Scatter plot de la satisfaction dans le temps
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.models import PredictionFeedback

class DashboardService:
    """Service pour générer les données et graphiques du dashboard"""
    
    @staticmethod
    def get_kpi_inference_time(db: Session) -> Dict:
        """
        Calcule le KPI du temps d'inférence moyen
        
        Returns:
            Dict avec temps moyen, min, max, et nombre de prédictions
        """
        result = db.query(
            func.avg(PredictionFeedback.inference_time_ms).label('avg_time'),
            func.min(PredictionFeedback.inference_time_ms).label('min_time'),
            func.max(PredictionFeedback.inference_time_ms).label('max_time'),
            func.count(PredictionFeedback.id).label('total_predictions')
        ).filter(
            PredictionFeedback.success == True
        ).first()
        
        return {
            'avg_inference_time_ms': round(float(result.avg_time), 2) if result.avg_time else 0,
            'min_inference_time_ms': int(result.min_time) if result.min_time else 0,
            'max_inference_time_ms': int(result.max_time) if result.max_time else 0,
            'total_predictions': int(result.total_predictions) if result.total_predictions else 0
        }
    
    @staticmethod
    def get_kpi_user_satisfaction(db: Session) -> Dict:
        """
        Calcule le KPI de satisfaction utilisateur
        
        Returns:
            Dict avec taux de satisfaction, nombre total de feedbacks
        """
        # Total des feedbacks renseignés (pas NULL)
        total_feedbacks = db.query(func.count(PredictionFeedback.id)).filter(
            PredictionFeedback.user_feedback.isnot(None),
            PredictionFeedback.rgpd_consent == True
        ).scalar() or 0
        
        # Feedbacks positifs (satisfaction = 1)
        positive_feedbacks = db.query(func.count(PredictionFeedback.id)).filter(
            PredictionFeedback.user_feedback == 1,
            PredictionFeedback.rgpd_consent == True
        ).scalar() or 0
        
        # Calcul du taux de satisfaction
        satisfaction_rate = round((positive_feedbacks / total_feedbacks * 100), 2) if total_feedbacks > 0 else 0
        
        return {
            'satisfaction_rate': satisfaction_rate,
            'positive_feedbacks': positive_feedbacks,
            'negative_feedbacks': total_feedbacks - positive_feedbacks,
            'total_feedbacks': total_feedbacks
        }
    
    @staticmethod
    def generate_inference_time_chart(db: Session) -> str:
        """
        Génère la courbe temporelle des temps d'inférence
        
        Returns:
            HTML du graphique Plotly
        """
        # Récupération de toutes les prédictions réussies
        predictions = db.query(
            PredictionFeedback.created_at,
            PredictionFeedback.inference_time_ms
        ).filter(
            PredictionFeedback.success == True
        ).order_by(
            PredictionFeedback.created_at
        ).all()
        
        if not predictions:
            return "<p>Aucune donnée disponible</p>"
        
        # Préparation des données
        timestamps = [p.created_at for p in predictions]
        inference_times = [p.inference_time_ms for p in predictions]
        
        # Création du graphique
        fig = go.Figure()
        
        # Ligne principale
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=inference_times,
            mode='lines+markers',
            name='Temps d\'inférence',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6)
        ))
        
        # Ligne de moyenne
        avg_time = sum(inference_times) / len(inference_times)
        fig.add_trace(go.Scatter(
            x=[timestamps[0], timestamps[-1]],
            y=[avg_time, avg_time],
            mode='lines',
            name=f'Moyenne ({avg_time:.0f} ms)',
            line=dict(color='#e74c3c', width=2, dash='dash')
        ))
        
        # Mise en forme
        fig.update_layout(
            title='Évolution du temps d\'inférence',
            xaxis_title='Date et heure',
            yaxis_title='Temps (ms)',
            hovermode='x unified',
            template='plotly_white',
            height=400,
            legend=dict(
                orientation="h",  # Légende horizontale
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    @staticmethod
    def generate_satisfaction_scatter(db: Session) -> str:
        """
        Génère le scatter plot de la satisfaction utilisateur
        
        Returns:
            HTML du graphique Plotly
        """
        # Récupération des feedbacks avec consentement RGPD
        feedbacks = db.query(
            PredictionFeedback.created_at,
            PredictionFeedback.user_feedback,
            PredictionFeedback.user_comment,
            PredictionFeedback.prediction_result
        ).filter(
            PredictionFeedback.rgpd_consent == True,
            PredictionFeedback.user_feedback.isnot(None)
        ).order_by(
            PredictionFeedback.created_at
        ).all()
        
        if not feedbacks:
            return "<p>Aucun feedback utilisateur disponible</p>"
        
        # Préparation des données
        timestamps = [f.created_at for f in feedbacks]
        satisfaction = [f.user_feedback for f in feedbacks]
        comments = [f.user_comment if f.user_comment else "NC" for f in feedbacks]  # Gestion des NULL
        predictions = [f.prediction_result for f in feedbacks]
        
        # Création du scatter plot
        fig = go.Figure()
        
        # Points satisfaits (1)
        satisfied_timestamps = [t for t, s in zip(timestamps, satisfaction) if s == 1]
        satisfied_predictions = [p for p, s in zip(predictions, satisfaction) if s == 1]
        satisfied_comments = [c for c, s in zip(comments, satisfaction) if s == 1]
        
        fig.add_trace(go.Scatter(
            x=satisfied_timestamps,
            y=[1] * len(satisfied_timestamps),
            mode='markers',
            name='Satisfait',
            marker=dict(
                size=12,
                color='#2ecc71',
                symbol='circle',
                line=dict(width=1, color='white')
            ),
            text=satisfied_predictions,
            customdata=satisfied_comments,
            hovertemplate='<b>Satisfait</b><br>Prédiction: %{text}<br>Commentaire: %{customdata}<br>Date: %{x}<extra></extra>'
        ))
        
        # Points insatisfaits (0)
        unsatisfied_timestamps = [t for t, s in zip(timestamps, satisfaction) if s == 0]
        unsatisfied_predictions = [p for p, s in zip(predictions, satisfaction) if s == 0]
        unsatisfied_comments = [c for c, s in zip(comments, satisfaction) if s == 0]
        
        fig.add_trace(go.Scatter(
            x=unsatisfied_timestamps,
            y=[0] * len(unsatisfied_timestamps),
            mode='markers',
            name='Pas satisfait',
            marker=dict(
                size=12,
                color='#e74c3c',
                symbol='x',
                line=dict(width=2)
            ),
            text=unsatisfied_predictions,
            customdata=unsatisfied_comments,
            hovertemplate='<b>Pas satisfait</b><br>Prédiction: %{text}<br>Commentaire: %{customdata}<br>Date: %{x}<extra></extra>'
        ))
        
        # Mise en forme
        fig.update_layout(
            title='Satisfaction utilisateur dans le temps',
            xaxis_title='Date et heure',
            yaxis=dict(
                tickmode='array',
                tickvals=[0, 1],
                ticktext=['Pas satisfait', 'Satisfait'],
                range=[-0.5, 1.5]
            ),
            hovermode='closest',
            template='plotly_white',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",  # Légende horizontale
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )
                
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    @staticmethod
    def get_dashboard_data(db: Session) -> Dict:
        """
        Récupère toutes les données nécessaires au dashboard
        
        Returns:
            Dict contenant KPIs et graphiques HTML
        """
        return {
            'kpi_inference': DashboardService.get_kpi_inference_time(db),
            'kpi_satisfaction': DashboardService.get_kpi_user_satisfaction(db),
            'chart_inference': DashboardService.generate_inference_time_chart(db),
            'chart_satisfaction': DashboardService.generate_satisfaction_scatter(db)
        }