import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
#from urllib.parse import quote_plus

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Import de la configuration
from config.settings import DB_URL, DB_URL_MASKED

# Configuration encodage pour Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Moteur SQLAlchemy
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,  # Vérifier la connexion avant utilisation
    echo=False  # True pour voir les requêtes SQL (à activer en développement)
)

print(f"🔗 Configuration de connexion : {DB_URL_MASKED}")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles ORM
Base = declarative_base()

def get_db():
    """Dépendance pour obtenir une session de base de données (pour FastAPI)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """Obtenir une session de base de données (utilisation directe)"""
    return SessionLocal()

def test_connection():
    """Tester la connexion à la base de données"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database(), current_user, version()"))
            row = result.fetchone()
            print(f"✅ Connexion réussie !")
            print(f"   📊 Base de données : {row[0]}")
            print(f"   👤 Utilisateur : {row[1]}")
            print(f"   🗄️  Version PostgreSQL : {row[2].split(',')[0]}")
            return True
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        print("💡 Vérifications :")
        print("   - PostgreSQL est-il démarré ?")
        print("   - La base de données existe-t-elle ?")
        print("   - L'utilisateur existe-t-il ?")
        print("   - Les variables d'environnement sont-elles correctes ?")
        return False

def create_tables():
    """Créer toutes les tables définies dans les modèles"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables : {e}")

if __name__ == "__main__":
    print("=== Test de connexion à la base de données ===")
    test_connection()