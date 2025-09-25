import sys
from pathlib import Path
import tensorflow as tf
from keras import layers, models

# Ajouter les chemins nécessaires
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import MODEL_CONFIG, MODELS_DIR
from src.data.preprocessing import clean_corrupted_images, setup_data_directory

class CatDogTrainer:
    def __init__(self):
        self.config = MODEL_CONFIG
        self.models_dir = MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
    def prepare_data(self):
        """Préparation des données"""
        # Configuration du répertoire de données
        data_path = setup_data_directory()
        
        # Nettoyage
        clean_corrupted_images(data_path)
        
        # Création des datasets
        train_ds, val_ds = tf.keras.utils.image_dataset_from_directory(
            data_path,
            validation_split=0.2,
            subset="both",
            seed=1337,
            image_size=self.config["image_size"],
            batch_size=self.config["batch_size"],
        )
        
        # Optimisations
        AUTOTUNE = tf.data.AUTOTUNE
        train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
        val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
        
        return train_ds, val_ds
    
    def create_model(self):
        """Création du modèle"""
        data_augmentation = tf.keras.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.1),
            layers.RandomZoom(0.1),
        ])
        
        inputs = tf.keras.Input(shape=self.config["image_size"] + (3,))
        x = layers.Rescaling(1.0/255)(inputs)
        x = data_augmentation(x)
        
        x = layers.Conv2D(32, 3, activation='relu')(x)
        x = layers.MaxPooling2D()(x)
        x = layers.Conv2D(64, 3, activation='relu')(x)
        x = layers.MaxPooling2D()(x)
        x = layers.Conv2D(128, 3, activation='relu')(x)
        x = layers.MaxPooling2D()(x)
        
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dropout(0.5)(x)
        outputs = layers.Dense(1, activation='sigmoid')(x)
        
        model = tf.keras.Model(inputs, outputs)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.config["learning_rate"]),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self):
        """Entraînement du modèle"""
        train_ds, val_ds = self.prepare_data()
        model = self.create_model()
        
        model_path = self.models_dir / "cats_dogs_model.keras"
        
        callbacks = [
            tf.keras.callbacks.ModelCheckpoint(
                model_path,
                save_best_only=True,
                monitor='val_accuracy',
                verbose=1
            ),
            tf.keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=3,
                restore_best_weights=True
            ),
        ]
        
        history = model.fit(
            train_ds,
            epochs=self.config["epochs"],
            callbacks=callbacks,
            validation_data=val_ds,
            verbose=1
        )
        
        print(f"Modèle sauvegardé: {model_path}")
        return model, history