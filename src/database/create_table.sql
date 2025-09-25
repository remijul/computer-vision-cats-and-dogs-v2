-- Se connecter à la base de données
\c cats_dogs_db;

-- Table pour stocker les métriques de prédictions avec feedback
CREATE TABLE IF NOT EXISTS predictions_feedback (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    inference_time_ms INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    prediction_result VARCHAR(10) NOT NULL CHECK (prediction_result IN ('cat', 'dog', 'error')),
    proba_cat DECIMAL(5,2) NOT NULL CHECK (proba_cat >= 0 AND proba_cat <= 100),
    proba_dog DECIMAL(5,2) NOT NULL CHECK (proba_dog >= 0 AND proba_dog <= 100),
    rgpd_consent BOOLEAN NOT NULL DEFAULT FALSE,
    filename VARCHAR(255) NULL,
    user_feedback INTEGER NULL CHECK (user_feedback IN (0, 1)),
    user_comment TEXT NULL
);

-- Index pour améliorer les performances des requêtes
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions_feedback(timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_result ON predictions_feedback(prediction_result);