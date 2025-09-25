#!/usr/bin/env python3
"""Script de lancement de l'API"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

if __name__ == "__main__":
    import uvicorn
    from config.settings import API_CONFIG
    
    print("Lancement de l'API Cats vs Dogs")
    print(f"URL: http://{API_CONFIG['host']}:{API_CONFIG['port']}")
    print(f"Docs: http://{API_CONFIG['host']}:{API_CONFIG['port']}/docs")
    
    uvicorn.run(
        "src.api.main:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=False  # En production Docker
    )