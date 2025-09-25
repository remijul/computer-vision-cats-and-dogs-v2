import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Chargement du fichier .env
load_dotenv()

# Chemins de base
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
CONFIG_DIR = ROOT_DIR / "config"

# Données
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
TEMP_DIR = Path(os.environ.get("TEMP_DIR", "/tmp/cats_dogs"))

# Base de données
## Récupération des variables d'environnement et Construction de l'URL PostgreSQL
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PWD = os.getenv('DB_PWD')
DB_PWD_ENCODED = quote_plus(DB_PWD) if DB_PWD else None # Encodage du mot de passe pour les caractères spéciaux
DB_URL = f"postgresql://{DB_USER}:{DB_PWD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DB_URL_MASKED = DB_URL.replace(DB_PWD_ENCODED, '***') if DB_PWD_ENCODED else DB_URL # Masquage du mdp dans l'URL (sert uniquement pour l'affichage dans le terminal, de manière sécurisée)
DB_TABLE_MONITORING = os.getenv('DB_TABLE_MONITORING')


# Modèles
MODELS_DIR = PROCESSED_DATA_DIR / "models" # SRC_DIR / "models/trained"

# Configuration du modèle
MODEL_CONFIG = {
    "image_size": (128, 128), # Optimized for speed-up
    "batch_size": 64,
    "epochs": 3, #10, # Optimized for speed-up
    "learning_rate": 0.001,
}

# Configuration API
API_TOKEN = os.getenv('API_TOKEN')
API_CONFIG = {
    "host": "127.0.0.1",
    "port": 8000,
    "token": API_TOKEN,
    "model_path": MODELS_DIR / "cats_dogs_model.keras",
}

# URLs de données
DATA_URLS = {
    "kaggle_cats_dogs": "https://download.microsoft.com/download/3/E/1/3E1C3F21-ECDB-4869-8368-6DEBA77B919F/kagglecatsanddogs_5340.zip"
}
