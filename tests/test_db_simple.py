#!/usr/bin/env python3
"""Tests pytest simples sur la base de données PostgreSQL"""

import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, inspect

# Configuration
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import DB_URL, DB_NAME, DB_TABLE_MONITORING

def test_database_connection():
    """Test de connexion à la base de données cats_dogs_db"""
    try:
        engine = create_engine(DB_URL)
        
        with engine.connect() as connection:
            # Test de connexion basique
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            assert test_value == 1
            
            # Vérification du nom de la base de données
            result = connection.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            assert db_name == DB_NAME
            
            print(f"\nConnexion réussie à la base: {db_name}")
            
    except Exception as e:
        pytest.fail(f"Connexion à la base de données échouée: {e}")

def test_predictions_feedback_table_exists():
    """Test de l'existence de la table predictions_feedback"""
    try:
        engine = create_engine(DB_URL)
        
        # Inspection de la base de données
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Vérification de l'existence de la table
        assert DB_TABLE_MONITORING in tables, "Table predictions_feedback non trouvée"
        
        print(f"\nTable predictions_feedback trouvée")
        print(f"Tables disponibles: {', '.join(sorted(tables))}")
        
    except Exception as e:
        pytest.fail(f"Vérification de la table échouée: {e}")

def test_predictions_feedback_table_structure():
    """Test de la structure de la table predictions_feedback"""
    try:
        engine = create_engine(DB_URL)
        
        with engine.connect() as connection:
            # Récupération des colonnes de la table
            result = connection.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{DB_TABLE_MONITORING}'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            column_names = [col[0] for col in columns]
            
            # Colonnes obligatoires attendues
            required_columns = [
                'id', 'created_at', 'inference_time_ms', 'success',
                'prediction_result', 'proba_cat', 'proba_dog',
                'rgpd_consent', 'filename', 'user_feedback', 
                'user_comment'
            ]
            
            # Vérification de l'existence des colonnes
            for col in required_columns:
                assert col in column_names, f"Colonne manquante: {col}"
            
            print(f"\nStructure de la table validée")
            print(f"Colonnes trouvées: {len(column_names)}")
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"  - {col[0]}: {col[1]} ({nullable})")
            
    except Exception as e:
        pytest.fail(f"Vérification de la structure échouée: {e}")

# Permet l'exécution directe du fichier
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])