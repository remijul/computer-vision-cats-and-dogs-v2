#!/usr/bin/env python3
"""Script d'entraînement du modèle"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.models.trainer import CatDogTrainer

def main():
    print("Début de l'entraînement du modèle Cats vs Dogs")
    
    trainer = CatDogTrainer()
    model, history = trainer.train()
    
    print("Entraînement terminé avec succès!")

if __name__ == "__main__":
    main()