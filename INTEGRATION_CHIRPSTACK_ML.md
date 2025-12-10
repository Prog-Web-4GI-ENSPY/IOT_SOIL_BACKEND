# 🔌 Intégration ChirpStack + Machine Learning

## 📋 Vue d'ensemble du Flux

Votre système fonctionne maintenant selon ce scénario :

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Capteurs   │─────>│  ChirpStack  │─────>│   Backend    │─────>│  Modèle ML   │
│   LoRaWAN    │      │   (Serveur)  │      │   FastAPI    │      │  (Service)   │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
                            │                      │                       │
                            │                      ▼                       │
                            │              ┌──────────────┐                │
                            │              │  PostgreSQL  │                │
                            │              │   Database   │                │
                            │              └──────────────┘                │
                            │                      │                       │
                            └──────────────────────┴───────────────────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────────┐
                                        │   Recommandations    │
                                        │    Automatiques      │
                                        └──────────────────────┘
```

## ✅ Configuration Actuelle

### 1. Services Créés

#### 📡 **ChirpStackService** (`app/services/chirpstack_service.py`)
- **Récupération des données** depuis ChirpStack API
- **Traitement automatique** des données uplink
- **Mise à jour du statut** des capteurs
- **Synchronisation** des devices

#### 🤖 **MLService** (`app/services/ml_service.py`)
- **Préparation des données** pour le modèle ML
- **Envoi automatique** au service ML
- **Création automatique** de recommandations
- **Génération de prédictions**

### 2. Endpoints Webhooks

#### 🔗 **POST `/api/v1/webhooks/chirpstack/uplink`**
**Webhook principal pour recevoir les données de ChirpStack**

**Ce qui se passe automatiquement :**
1. Réception des données du capteur
2. Stockage dans `sensor_measurements`
3. Mise à jour du statut du capteur
4. **Envoi automatique au ML (en arrière-plan)**
5. **Création automatique de recommandations**

**Configuration dans ChirpStack :**
```
Applications > [Votre App] > Integrations > Add HTTP Integration
URL: https://votre-domaine.com/api/v1/webhooks/chirpstack/uplink
Method: POST
```

#### 🔗 **POST `/api/v1/webhooks/chirpstack/join`**
Webhook pour les événements de connexion (join) des devices

#### 🔗 **POST `/api/v1/webhooks/chirpstack/status`**
Webhook pour les événements de statut (batterie, etc.)

#### 🚀 **POST `/api/v1/webhooks/ml/trigger/{capteur_id}`**
Déclencher manuellement une analyse ML pour un capteur

#### 🔄 **POST `/api/v1/webhooks/ml/batch-analysis`**
Analyser tous les capteurs de l'utilisateur en une fois

#### 🔄 **GET `/api/v1/webhooks/chirpstack/sync-devices`**
Synchroniser les devices depuis ChirpStack

## 🔧 Configuration Requise

### 1. Variables d'Environnement (`.env`)

```bash
# ChirpStack
CHIRPSTACK_API_URL=https://your-chirpstack-server.com/api
CHIRPSTACK_API_TOKEN=your-api-token-here
CHIRPSTACK_APPLICATION_ID=your-application-id

# Machine Learning Service
ML_API_URL=http://localhost:5000
ML_API_TIMEOUT=60
```

### 2. Format des Données ChirpStack

**Données envoyées par ChirpStack au webhook :**
```json
{
  "devEUI": "0123456789abcdef",
  "data": {
    "temperature": 25.5,
    "humidity": 65.0,
    "soilMoisture": 45.0,
    "ph": 6.5,
    "nitrogen": 50,
    "phosphorus": 30,
    "potassium": 40,
    "lightIntensity": 800,
    "batteryVoltage": 3.7
  },
  "rxInfo": [{
    "rssi": -80,
    "loRaSNR": 8.5
  }],
  "txInfo": {
    "frequency": 868100000
  }
}
```

### 3. Format Attendu par le Modèle ML

**Requête vers le ML (`POST /api/predict`) :**
```json
{
  "capteur_info": {
    "id": "uuid",
    "type": "multi-sensor",
    "dev_eui": "0123456789abcdef"
  },
  "parcelle_info": {
    "id": "uuid",
    "superficie": 2.5,
    "type_sol": "Argileux",
    "culture_actuelle": "Maïs"
  },
  "measurements": [
    {
      "timestamp": "2025-12-10T10:30:00",
      "temperature": 25.5,
      "humidity": 65.0,
      "soil_moisture": 45.0,
      ...
    }
  ],
  "statistics": {
    "temperature": {
      "mean": 24.8,
      "min": 18.0,
      "max": 32.0,
      "count": 100
    },
    ...
  }
}
```

**Réponse du ML :**
```json
{
  "titre": "Irrigation recommandée",
  "description": "L'humidité du sol est faible. Irrigation de 20mm recommandée.",
  "priorite": "Urgent",
  "confidence": 0.85,
  "model_version": "v1.0",
  "prediction": {
    "type": "yield",
    "valeur_predite": 4500,
    "confiance": 0.78
  }
}
```

## 🚀 Démarrage

### 1. Lancer le Backend FastAPI

```bash
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Lancer votre Service ML

```bash
# Exemple si votre ML est en Python Flask
python ml_service/app.py
```

### 3. Configurer ChirpStack

1. Accéder à votre interface ChirpStack
2. Aller dans **Applications** > **[Votre Application]** > **Integrations**
3. Ajouter une **HTTP Integration**
4. URL: `https://votre-domaine.com/api/v1/webhooks/chirpstack/uplink`
5. Sauvegarder

## 📊 Flux Automatique Complet

### Scénario : Réception de Nouvelles Données

1. **Capteur LoRaWAN** envoie des données à ChirpStack
2. **ChirpStack** forwarde au webhook `/webhooks/chirpstack/uplink`
3. **Backend** :
   - Crée un enregistrement `SensorMeasurements`
   - Met à jour le statut du `Capteur` (online, batterie, signal)
   - Lance le traitement ML en arrière-plan
4. **Service ML** :
   - Reçoit les 100 dernières mesures + statistiques
   - Analyse les données
   - Retourne une recommandation
5. **Backend** :
   - Crée automatiquement une `Recommendation`
   - Crée une `Prediction` si applicable
   - Stocke tout dans la base de données

### Résultat

L'utilisateur retrouve automatiquement :
- ✅ Nouvelles mesures dans `/api/v1/sensor-data/`
- ✅ Nouvelles recommandations dans `/api/v1/recommendations/`
- ✅ Nouvelles prédictions dans `/api/v1/predictions/`
- ✅ Statut capteur mis à jour dans `/api/v1/capteurs/{id}`

## 🔍 Tests

### 1. Tester le Webhook Manuellement

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/chirpstack/uplink \
  -H "Content-Type: application/json" \
  -d '{
    "devEUI": "votre-dev-eui",
    "data": {
      "temperature": 25.5,
      "humidity": 65.0,
      "soilMoisture": 45.0
    }
  }'
```

### 2. Déclencher une Analyse ML

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/ml/trigger/{capteur_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Vérifier le Statut

```bash
curl http://localhost:8000/api/v1/webhooks/status
```

## 📝 Notes Importantes

1. **Le service ML doit être démarré** et accessible à `ML_API_URL`
2. **ChirpStack doit être configuré** avec l'URL correcte du webhook
3. **Les capteurs doivent être enregistrés** dans la base de données avec leur `dev_eui`
4. **Minimum 10 mesures** sont nécessaires pour déclencher l'analyse ML automatique

## 🎯 Endpoints Disponibles

Total : **91 routes** incluant :
- 11 endpoints pour les capteurs
- 9 endpoints pour les données de capteurs
- 7 endpoints pour les recommandations
- 7 endpoints pour les prédictions
- **7 nouveaux endpoints pour webhooks et ML**

## ✅ Conclusion

Votre configuration est maintenant **entièrement fonctionnelle** pour :
- ✅ Recevoir automatiquement les données de ChirpStack
- ✅ Envoyer automatiquement au modèle ML
- ✅ Générer automatiquement des recommandations
- ✅ Créer des prédictions basées sur les données

**Commande pour lancer :**
```bash
source venv/bin/activate && uvicorn main:app --reload
```
