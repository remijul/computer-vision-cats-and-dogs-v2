import os
import subprocess
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Import de la configuration
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PWD, DB_PWD_ENCODED

# Import du connecteur (après chargement des variables d'env)
# Si le script de connexion (db_connector.py) n'existe pas alors utilisation d'une méthode simplifiée et directe (fallback)
try:
    from db_connector import test_connection
    CONNECTOR_AVAILABLE = True
except ImportError:
    CONNECTOR_AVAILABLE = False
    print("⚠️  db_connector.py non disponible, test de connexion basique")

def create_table():
    """Crée la table de monitoring via psql"""
    try:
        # Chemin absolu du fichier SQL
        current_dir = Path(__file__).parent
        sql_file = current_dir / 'create_table.sql'
        
        # Vérification que le fichier existe
        if not sql_file.exists():
            print(f"❌ Fichier SQL non trouvé: {sql_file}")
            return False
        
        # Commande psql pour exécuter le script SQL
        cmd = [
            'psql',
            '-h', DB_HOST,
            '-p', DB_PORT,
            '-d', DB_NAME,
            '-U', 'postgres',
            '-f', str(sql_file)
        ]
        
        print("🔨 Création de la table de monitoring...")
        # Info : subprocess.run() permet d'exécuter des commandes système depuis Python
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print("✅ Table de monitoring créée avec succès")
            return True
        else:
            print(f"❌ Erreur: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        return False

def test_connection_basic():
    """Test de connexion basique sans db_connector"""
    try:
        from sqlalchemy import create_engine, text
        
        db_url = f"postgresql://{DB_USER}:{DB_PWD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user"))
            row = result.fetchone()
            print(f"✅ Connexion réussie ! Base: {row[0]}, Utilisateur: {row[1]}")
            return True
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def main():
    """Fonction principale"""
    print("=== Création de la table de monitoring ===")
    
    # Vérification des variables d'environnement
    if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PWD]):
        print("❌ Variables d'environnement manquantes")
        print("💡 Vérifiez votre fichier .env")
        return
    
    print(f"📊 Base de données : {DB_NAME}")
    print(f"👤 Utilisateur : {DB_USER}")
    print(f"🌐 Hôte : {DB_HOST}:{DB_PORT}")
    
    # Création de la base de données
    if create_table():
        print("\n--- Test de connexion ---")
        
        # Utilisation du connecteur si disponible, sinon test basique
        if CONNECTOR_AVAILABLE:
            print("🔗 Test avec db_connector.py")
            success = test_connection()
        else:
            print("🔗 Test de connexion basique")
            success = test_connection_basic()
        
        if success:
            print("\n🎉 Table de monitoring prête à l'emploi !")
            if CONNECTOR_AVAILABLE:
                print("💡 Vous pouvez maintenant utiliser db_connector.py dans vos applications")
    
    print("\n=== Terminé ===")

if __name__ == "__main__":
    main()