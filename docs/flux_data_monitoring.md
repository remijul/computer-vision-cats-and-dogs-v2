# Analyse du flux de données : De l'interface web à la base de données

## Vue d'ensemble du processus

Le système de collecte de feedback dans la V2 implique une chaîne complexe de transfert de données entre plusieurs couches technologiques. Cette note analyse le parcours complet des informations depuis l'interface utilisateur jusqu'au stockage en base de données.

## Architecture du flux de données

### Couches impliquées

1. **Couche Présentation** : Template Jinja2 (inference.html)
2. **Couche Client** : JavaScript côté navigateur
3. **Couche API** : FastAPI (routes.py)
4. **Couche Métier** : Services Python (feedback_service.py)
5. **Couche Données** : PostgreSQL via SQLAlchemy

### Schéma du flux

```txt
[Interface Web] → [JavaScript] → [API FastAPI] → [Service Python] → [Base PostgreSQL]
```

## Analyse détaillée par étapes

### Étape 1 : Collecte des données utilisateur (inference.html)

#### Éléments collectés

- Fichier image via `<input type="file">`
- Consentement RGPD via `<input type="checkbox" id="rgpdConsent">`
- Feedback satisfaction via boutons `submitFeedback(1)` ou `submitFeedback(0)`
- Commentaire optionnel via `<textarea id="userComment">`

#### Mécanisme

Le template Jinja2 génère des formulaires HTML avec des identifiants uniques permettant au JavaScript de récupérer les valeurs.

#### Code HTML concerné (`inference.html`)

```html
<!-- Formulaire principal -->
<form id="predictionForm" enctype="multipart/form-data">
    <div class="mb-3">
        <label for="imageFile" class="form-label">Choisir une image</label>
        <input type="file" class="form-control" id="imageFile" accept="image/*" required>
    </div>
    
    <!-- Section RGPD -->
    <div class="mb-3 p-3 bg-light border-start border-warning border-4">
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="rgpdConsent">
            <label class="form-check-label" for="rgpdConsent">
                <strong>Consentement RGPD :</strong> J'accepte que mes données soient stockées
            </label>
        </div>
    </div>
</form>

<!-- Section Feedback utilisateur -->
<div id="feedbackSection" class="mt-4 p-3 bg-light rounded" style="display: none;">
    <div class="btn-group mb-3" role="group">
        <button type="button" class="btn btn-outline-success" onclick="submitFeedback(1)">
            Satisfait
        </button>
        <button type="button" class="btn btn-outline-danger" onclick="submitFeedback(0)">
            Pas satisfait
        </button>
    </div>
    
    <div class="mb-3">
        <label for="userComment" class="form-label">Commentaire optionnel</label>
        <textarea class="form-control" id="userComment" rows="3"></textarea>
    </div>
    
    <button type="button" class="btn btn-secondary btn-sm" onclick="submitComment()">
        Envoyer le commentaire
    </button>
</div>
```

### Étape 2 : Traitement côté client (JavaScript)

#### Transformations réalisées

- Création d'un objet FormData pour encapsuler les données
- Conversion du consentement RGPD en booléen
- Préparation de la requête HTTP multipart/form-data

#### Variables JavaScript critiques

- `currentFeedbackId` : Stockage de l'identifiant de prédiction retourné
- `rgpdConsent` : État du consentement utilisateur

#### Fonction principale de prédiction

```js
// Variable globale pour stocker l'ID du feedback
let currentFeedbackId = null;

// Soumission du formulaire de prédiction
document.getElementById('predictionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('imageFile');
    const rgpdConsent = document.getElementById('rgpdConsent').checked;
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Veuillez sélectionner une image');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('rgpd_consent', rgpdConsent);
        
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Stockage de l'ID du feedback
            currentFeedbackId = data.feedback_id;
            
            // Affichage des résultats
            // ... code d'affichage
            
            // Affichage de la section feedback si RGPD accepté
            if (rgpdConsent && currentFeedbackId) {
                document.getElementById('feedbackSection').style.display = 'block';
            }
        }
    } catch (error) {
        alert('Erreur de communication avec le serveur');
        console.error(error);
    }
});
```

#### Fonctions de feedback

```js
// Envoi du feedback (satisfait/pas satisfait)
async function submitFeedback(feedbackValue) {
    if (!currentFeedbackId) {
        alert('Aucune prédiction active');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('feedback_id', currentFeedbackId);
        formData.append('user_feedback', feedbackValue);
        
        const response = await fetch('/api/update-feedback', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const feedbackText = feedbackValue === 1 ? 
                'Merci pour votre retour positif !' : 
                'Merci pour votre retour.';
            
            // Affichage du message de confirmation
            // ... code d'affichage
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Envoi du commentaire
async function submitComment() {
    if (!currentFeedbackId) return;
    
    const commentInput = document.getElementById('userComment');
    const comment = commentInput.value.trim();
    
    if (!comment) {
        alert('Veuillez saisir un commentaire');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('feedback_id', currentFeedbackId);
        formData.append('user_comment', comment);
        
        const response = await fetch('/api/update-feedback', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Confirmation et nettoyage
            commentInput.value = '';
            commentInput.disabled = true;
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}
```

### Étape 3 : Transmission vers l'API (FastAPI)

#### Paramètres transmis

- file: UploadFile : Fichier image
- rgpd_consent: bool : Consentement RGPD
- token : Token d'authentification (header)

#### Format de transmission

La requête utilise le format multipart/form-data, géré automatiquement par FastAPI via les types UploadFile et Form.

#### Endpoint principal : `/api/predict`

```py
@router.post("/api/predict")
async def predict_api(
    file: UploadFile = File(...),
    rgpd_consent: bool = Form(False),
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """API de prédiction avec enregistrement en base de données"""
    if not predictor.is_loaded():
        raise HTTPException(status_code=503, detail="Modèle non disponible")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Format d'image invalide")
    
    # Mesure du temps de début
    start_time = time.perf_counter()
    
    try:
        # Lecture de l'image
        image_data = await file.read()
        
        # Prédiction
        result = predictor.predict(image_data)
        
        # Calcul du temps d'inférence en millisecondes
        end_time = time.perf_counter()
        inference_time_ms = int((end_time - start_time) * 1000)
        
        # Extraction des probabilités (conversion en pourcentage)
        proba_cat = result['probabilities']['cat'] * 100
        proba_dog = result['probabilities']['dog'] * 100
        
        # Enregistrement en base de données
        feedback_record = FeedbackService.save_prediction_feedback(
            db=db,
            inference_time_ms=inference_time_ms,
            success=True,
            prediction_result=result["prediction"].lower(),  # 'cat' ou 'dog'
            proba_cat=proba_cat,
            proba_dog=proba_dog,
            rgpd_consent=rgpd_consent,
            filename=file.filename if rgpd_consent else None,
            user_feedback=None,  # Sera mis à jour plus tard
            user_comment=None    # Sera mis à jour plus tard
        )
        
        # Préparation de la réponse
        response_data = {
            "filename": file.filename,
            "prediction": result["prediction"],
            "confidence": f"{result['confidence']:.2%}",
            "probabilities": {
                "cat": f"{result['probabilities']['cat']:.2%}",
                "dog": f"{result['probabilities']['dog']:.2%}"
            },
            "inference_time_ms": inference_time_ms,
            "feedback_id": feedback_record.id  # ID pour les mises à jour ultérieures
        }
        
        return response_data
        
    except Exception as e:
        # Gestion d'erreur avec enregistrement
        end_time = time.perf_counter()
        inference_time_ms = int((end_time - start_time) * 1000)
        
        FeedbackService.save_prediction_feedback(
            db=db,
            inference_time_ms=inference_time_ms,
            success=False,
            prediction_result="cat",  # Valeur par défaut pour respecter la contrainte
            proba_cat=0.0,
            proba_dog=0.0,
            rgpd_consent=False,
            user_comment=str(e)
        )
        
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction: {str(e)}")
```

#### Endpoint de mise à jour `/api/update-feedback`

```py
@router.post("/api/update-feedback")
async def update_feedback(
    feedback_id: int = Form(...),
    user_feedback: int = Form(None),
    user_comment: str = Form(None),
    db: Session = Depends(get_db)
):
    """Mise à jour du feedback utilisateur"""
    try:
        from src.database.models import PredictionFeedback
        
        # Récupération de l'enregistrement
        record = db.query(PredictionFeedback).filter(
            PredictionFeedback.id == feedback_id
        ).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Feedback non trouvé")
        
        # Mise à jour uniquement si RGPD accepté
        if not record.rgpd_consent:
            raise HTTPException(
                status_code=403,
                detail="Consentement RGPD non accepté"
            )
        
        # Mise à jour des champs
        if user_feedback is not None:
            if user_feedback not in [0, 1]:
                raise HTTPException(status_code=400, detail="user_feedback doit être 0 ou 1")
            record.user_feedback = user_feedback
        
        if user_comment:
            record.user_comment = user_comment
        
        # Sauvegarde en base
        db.commit()
        
        return {"success": True, "message": "Feedback mis à jour avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
```

### Étape 4 : Traitement dans l'API (`routes.py`)

#### Opérations séquentielles

- Validation des entrées : Vérification du format d'image et de l'authentification
- Prédiction IA : Appel du modèle CNN via `predictor.predict()`
- Calcul des métriques : Mesure du temps d'inférence
- Préparation des données : Formatage pour la base de données
- Appel du service : Utilisation de `FeedbackService.save_prediction_feedback()`

#### Transformations critiques

- Conversion des probabilités en pourcentage (× 100)
- Gestion conditionnelle des données selon le consentement RGPD
- Création de l'objet de réponse avec `feedback_id`

#### Service métier (`feedback_service.py`)

```py
@staticmethod
def save_prediction_feedback(
    db: Session,
    inference_time_ms: int,
    success: bool,
    prediction_result: str,
    proba_cat: float,
    proba_dog: float,
    rgpd_consent: bool,
    filename: str = None,
    user_feedback: int = None,
    user_comment: str = None
) -> PredictionFeedback:
    """Enregistre une prédiction avec feedback dans la base de données"""
    
    # Si pas de consentement RGPD, on ne stocke pas les données personnelles
    if not rgpd_consent:
        filename = None
        user_feedback = None
        user_comment = None
    
    # Création de l'enregistrement
    feedback = PredictionFeedback(
        inference_time_ms=inference_time_ms,
        success=success,
        prediction_result=prediction_result,
        proba_cat=round(proba_cat, 2),
        proba_dog=round(proba_dog, 2),
        rgpd_consent=rgpd_consent,
        filename=filename,
        user_feedback=user_feedback,
        user_comment=user_comment
    )
    
    # Enregistrement en base
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return feedback
```

### Étape 5 : Service métier (`feedback_service.py`)

#### Méthode clé : `save_prediction_feedback()`

#### Logique de traitement RGPD

```python
if not rgpd_consent:
    filename = None
    user_feedback = None
    user_comment = None
```

#### Création de l'objet SQLAlchemy

L'objet `PredictionFeedback` est instancié avec tous les paramètres, puis persisté via `db.commit()`.

### Étape 6 : Stockage en base (PostgreSQL)

#### Table cible : `predictions_feedback`

#### Contraintes appliquées

- Vérification des valeurs de probabilité (0-100)
- Validation du résultat de prédiction ('cat', 'dog', 'error')
- Contrôle du feedback utilisateur (0, 1, ou NULL)

## Points de complexité identifiés

### 1. Gestion asynchrone JavaScript-API

**Problématique** : La communication entre JavaScript et FastAPI utilise des promesses async/await, créant une complexité dans la gestion des erreurs et des états.

**Solution adoptée** : Utilisation de try-catch avec gestion différenciée des erreurs réseau et serveur.

### 2. Synchronisation des identifiants

**Problématique** : Le `feedback_id` généré côté serveur doit être conservé côté client pour les mises à jour ultérieures.

**Solution adoptée** : Variable globale JavaScript `currentFeedbackId` mise à jour après chaque prédiction.

### 3. Conformité RGPD multi-couches

**Problématique** : Le consentement RGPD doit être respecté à tous les niveaux (JavaScript, API, base de données).

**Solution adoptée** : Vérifications redondantes à chaque étape avec nullification des données personnelles si pas de consentement.

### 4. Gestion des types de données

**Problématique** : Conversion entre types JavaScript (string, boolean) et types Python (int, bool, str).

**Solution adoptée** : Validation explicite avec FastAPI Pydantic models et conversion manuelle quand nécessaire.

## Bonnes pratiques observées

### Séparation des responsabilités

- Frontend : Collecte et validation basique
- API : Validation métier et orchestration
- Service : Logique métier pure
- Base : Contraintes d'intégrité

### Gestion d'erreurs en cascade

- JavaScript : Affichage d'alertes utilisateur
- FastAPI : Codes HTTP standardisés
- Service : Exceptions Python typées
- Base : Contraintes SQL avec messages explicites

### Sécurité

- Authentification par token
- Validation des types de fichiers
- Échappement automatique des données (SQLAlchemy)

## Conclusion

Ce flux de données illustre les défis typiques d'une application web moderne full-stack. La complexité réside moins dans chaque composant individuel que dans leur intégration harmonieuse et la gestion cohérente des états à travers toutes les couches.

Ce cas d'usage démontre l'importance de :

- La conception d'APIs bien définies
- La validation redondante mais intelligente
- La gestion explicite des erreurs
- Le respect des contraintes légales (RGPD) dans l'architecture technique

Cette architecture prépare naturellement l'évolution vers des systèmes plus complexes (microservices, event-driven architecture) tout en restant compréhensible et maintenable.
