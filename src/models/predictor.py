import sys
from pathlib import Path
import tensorflow as tf
import numpy as np
from PIL import Image
import io

# Ajouter les chemins nécessaires
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import MODEL_CONFIG, API_CONFIG

class CatDogPredictor:
    def __init__(self):
        self.image_size = MODEL_CONFIG["image_size"]
        self.model_path = API_CONFIG["model_path"]
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Chargement du modèle"""
        try:
            if self.model_path.exists():
                self.model = tf.keras.models.load_model(self.model_path)
                print(f"Modèle chargé: {self.model_path}")
            else:
                print(f"Modèle non trouvé: {self.model_path}")
        except Exception as e:
            print(f"Erreur de chargement du modèle: {e}")
            self.model = None
    
    def preprocess_image(self, image_data: bytes):
        """Préprocessing de l'image"""
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image = image.resize(self.image_size)
        img_array = np.array(image)
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    def predict(self, image_data: bytes):
        """Prédiction"""
        if self.model is None:
            raise ValueError("Modèle non chargé")
        
        processed_image = self.preprocess_image(image_data)
        prediction = self.model.predict(processed_image, verbose=0)
        score = float(prediction[0][0])
        
        if score > 0.5:
            predicted_class = "Dog"
            confidence = score
        else:
            predicted_class = "Cat"
            confidence = 1 - score
        
        return {
            "prediction": predicted_class,
            "confidence": confidence,
            "probabilities": {
                "cat": 1 - score,
                "dog": score
            },
            "raw_score": score
        }
    
    def is_loaded(self):
        """Vérifier si le modèle est chargé"""
        return self.model is not None