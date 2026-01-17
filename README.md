# 🌱 AgroPredict Backend API


**AgroPredict-Backend** est le cerveau d'une solution d'agriculture intelligente (Smart Farming) conçue pour optimiser le rendement des cultures. Il s'agit d'une **API RESTful** puissante et évolutive, construite pour collecter des données de capteurs IoT, exécuter des modèles de prédiction agronomique (rendement, risques), et générer des recommandations d'actions précises pour les agriculteurs .

Ce projet a été réalisé dans le cadre de l'**Unité d'Enseignement (UE) Électronique et Interfaçage** en 4ème année de Génie Informatique à l'**École Nationale Supérieure Polytechnique de Yaoundé (ENSPY)**.

---

## 📋 Table des matières

- [Objectifs clés](#objectifs-cles)
- [Vue d'ensemble](#vue-densemble)
- [Technologies](#technologies)
- [Installation](#installation)
- [Configuration](#configuration)
- [Structure du projet](#structure-du-projet)
- [API Endpoints](#api-endpoints)
- [Base de données](#base-de-données)
- [Sécurité](#sécurité)
- [Tests](#tests)
- [Déploiement](#déploiement)

---
## 🎯 Objectifs Clés

  * **Intégration IoT :** Recevoir et traiter les données en temps réel provenant des capteurs de sol et environnementaux (via des systèmes comme ChirpStack/LoRaWAN).
  * **Modélisation Agronomique :** Fournir des *endpoints* pour des **prédictions** basées sur des modèles d'apprentissage automatique (ML) intégrant les données de capteurs et les informations de parcelle.
  * **Système de Recommandation :** Générer des **recommandations** d'irrigation, de fertilisation ou de gestion des maladies.
  * **Base de Données Robuste :** Gérer les utilisateurs, les terrains, les parcelles, les capteurs, et toutes les données historiques.
  
## 🎯 Vue d'ensemble

AgroPredict Backend est une API REST qui gère :
- 👤 Authentification et gestion des utilisateurs
- 🗺️ Localités et terrains agricoles
- 📦 Parcelles et caractéristiques du sol
- 📡 Capteurs LoRaWAN via ChirpStack
- 📊 Données capteurs en temps réel
- 🌾 Catalogue de cultures
- 🤖 Prédictions de cultures (IA/ML)
- 💡 Recommandations agronomiques
- 🔔 Alertes et notifications

---

## 🚀 Technologies

- **Framework**: FastAPI 0.109+
- **Base de données**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Validation**: Pydantic 2.5+
- **Authentification**: JWT (python-jose)
- **Sécurité**: Passlib + bcrypt
- **HTTP Client**: HTTPX (pour ChirpStack)
- **IoT**: LoRaWAN via ChirpStack
- **Tests**: Pytest

---

## 🔧 Installation

### Prérequis

- Python 3.11+
- PostgreSQL 15+
- ChirpStack Server (pour IoT)

### Installation locale

```bash
# Cloner le repository
git clone https://github.com/Prog-Web-4GI-ENSPY/IOT_SOIL_BACKEND.git
cd IOT_SOIL_BACKEND

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env avec vos configurations
nano .env
```

---

## ⚙️ Configuration

### Variables d'environnement (`.env`)

```env
# Application
APP_NAME=AgroPredict API
APP_VERSION=1.0.0
DEBUG=False
API_V1_PREFIX=/api/v1

# Database
POSTGRES_USER=agropredict_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agropredict_db
DATABASE_URL=postgresql://user:password@localhost:5432/agropredict

# Security
SECRET_KEY=votre-clé-secrète-très-longue-et-sécurisée-changez-moi
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ChirpStack Configuration
CHIRPSTACK_API_URL=https://your-chirpstack.com/api
CHIRPSTACK_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
CHIRPSTACK_APPLICATION_ID=your-app-id

# CORS Origins
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://agropredict.com"]

# Email (optionnel)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
EMAILS_FROM_EMAIL=noreply@agropredict.com

# Redis (optionnel - pour cache)
REDIS_URL=redis://localhost:6379/0

# Sentry (optionnel - monitoring)
SENTRY_DSN=https://your-sentry-dsn
```

### Configuration de la base de données

```bash
# Créer la base de données
createdb agropredict

# Ou via psql
psql -U postgres
CREATE DATABASE agropredict;
CREATE USER agropredict_user WITH PASSWORD 'votre_password';
GRANT ALL PRIVILEGES ON DATABASE agropredict TO agropredict_user;
\q
```

### Migrations

```bash
# Initialiser Alembic (si pas déjà fait)
alembic init alembic

# Créer une migration
alembic revision --autogenerate -m "Initial migration"

# Appliquer les migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1

# Voir l'historique
alembic history
```

---

## 🏗️ Structure du projet

```
agropredict-backend/
│
├── README.md
├── requirements.txt
├── .env.example
├── .env
├── .gitignore
├── alembic.ini
├── main.py
│
├── app/
│   ├── __init__.py
│   ├── database.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration centralisée
│   │   └── security.py        # Sécurité et JWT
│   │
│   ├── models/                # Modèles SQLAlchemy
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── location.py
│   │   ├── terrain.py
│   │   ├── parcelle.py
│   │   ├── capteur.py
│   │   ├── sensor_data.py
│   │   ├── culture.py
│   │   ├── prediction.py
│   │   ├── recommendation.py
│   │   └── alert.py
│   │
│   ├── schemas/               # Schémas Pydantic
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── user.py
│   │   ├── location.py
│   │   ├── terrain.py
│   │   ├── parcelle.py
│   │   ├── capteur.py
│   │   ├── sensor_data.py
│   │   ├── culture.py
│   │   ├── prediction.py
│   │   ├── recommendation.py
│   │   └── alert.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py            # Dépendances (auth, db)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py      # Router principal
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── localites.py
│   │       ├── terrains.py
│   │       ├── parcelles.py
│   │       ├── capteurs.py
│   │       ├── sensor_data.py
│   │       ├── cultures.py
│   │       ├── predictions.py
│   │       ├── recommendations.py
│   │       └── alerts.py
│   │
│   ├── services/              # Logique métier
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── terrain.py
│   │   ├── parcelle.py
│   │   ├── chirpstack.py
│   │   ├── prediction.py
│   │   ├── recommendation.py
│   │   └── email.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── geometry.py        # Calculs géométriques
│       ├── validators.py
│       └── helpers.py
│
├── alembic/
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_terrains.py
│   └── test_predictions.py
│
└── scripts/
    ├── init_db.py             # Script d'initialisation
    └── seed_data.py           # Données de test
```

---

## 🛣️ API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Authentification

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/auth/register` | Inscription |
| POST | `/auth/login` | Connexion (retourne JWT) |
| POST | `/auth/refresh` | Rafraîchir le token |
| POST | `/auth/reset-password` | Demande de réinitialisation |
| POST | `/auth/reset-password/confirm` | Confirmer réinitialisation |
| GET | `/auth/me` | Utilisateur connecté |

### Utilisateurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/users` | Liste utilisateurs (admin) |
| GET | `/users/{id}` | Détail utilisateur |
| PUT | `/users/{id}` | Modifier utilisateur |
| DELETE | `/users/{id}` | Supprimer utilisateur (admin) |

### Localités

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/localites` | Liste localités |
| POST | `/localites` | Créer localité |
| GET | `/localites/{id}` | Détail localité |
| PUT | `/localites/{id}` | Modifier localité |
| DELETE | `/localites/{id}` | Supprimer localité |

### Terrains

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/terrains` | Liste terrains |
| POST | `/terrains` | Créer terrain |
| GET | `/terrains/{id}` | Détail terrain |
| PUT | `/terrains/{id}` | Modifier terrain |
| DELETE | `/terrains/{id}` | Supprimer terrain |
| GET | `/terrains/{id}/parcelles` | Parcelles du terrain |

### Parcelles

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/parcelles` | Liste parcelles |
| POST | `/parcelles` | Créer parcelle |
| GET | `/parcelles/{id}` | Détail parcelle |
| PUT | `/parcelles/{id}` | Modifier parcelle |
| DELETE | `/parcelles/{id}` | Supprimer parcelle |
| GET | `/parcelles/{id}/capteurs` | Capteurs de la parcelle |
| GET | `/parcelles/{id}/historique` | Historique cultures |

### Capteurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/capteurs` | Liste capteurs |
| POST | `/capteurs` | Créer capteur |
| GET | `/capteurs/{id}` | Détail capteur |
| PUT | `/capteurs/{id}` | Modifier capteur |
| DELETE | `/capteurs/{id}` | Supprimer capteur |
| GET | `/capteurs/{id}/data` | Données du capteur |
| GET | `/capteurs/{id}/status` | Statut capteur |

### Données Capteurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/sensor-data/webhook/chirpstack` | Webhook ChirpStack |
| GET | `/sensor-data/capteurs/{id}` | Données d'un capteur |
| GET | `/sensor-data/parcelles/{id}` | Données d'une parcelle |
| GET | `/sensor-data/statistics` | Statistiques |

### Cultures

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/cultures` | Liste cultures |
| POST | `/cultures` | Créer culture (admin) |
| GET | `/cultures/{id}` | Détail culture |
| PUT | `/cultures/{id}` | Modifier culture (admin) |
| DELETE | `/cultures/{id}` | Supprimer culture (admin) |
| GET | `/cultures/search` | Rechercher cultures |

### Prédictions

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/predictions` | Créer prédiction |
| GET | `/predictions/{id}` | Détail prédiction |
| GET | `/predictions/user/{user_id}` | Prédictions utilisateur |
| GET | `/predictions/parcelle/{parcelle_id}` | Prédictions parcelle |

### Recommandations

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/recommendations` | Liste recommandations |
| GET | `/recommendations/{id}` | Détail recommandation |
| PUT | `/recommendations/{id}/status` | Changer statut |
| GET | `/recommendations/parcelle/{id}` | Recommandations parcelle |
| GET | `/recommendations/urgent` | Recommandations urgentes |

### Alertes

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/alerts` | Liste alertes |
| GET | `/alerts/{id}` | Détail alerte |
| PUT | `/alerts/{id}/read` | Marquer comme lue |
| PUT | `/alerts/{id}/resolve` | Résoudre alerte |
| DELETE | `/alerts/{id}` | Supprimer alerte |

---

## 🔐 Sécurité

### Authentification JWT

```python
# Exemple d'utilisation
from app.api.deps import get_current_user, get_current_active_user

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_active_user)
):
    return {"message": f"Hello {current_user.email}"}
```

### Hash des mots de passe

```python
from app.core.security import get_password_hash, verify_password

# Hasher un mot de passe
hashed = get_password_hash("mon_password")

# Vérifier un mot de passe
is_valid = verify_password("mon_password", hashed)
```

### Permissions

```python
from app.api.deps import require_admin

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    # Seuls les admins peuvent accéder
    pass
```

---

## 🧪 Tests

### Lancer les tests

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov=app tests/

# Tests spécifiques
pytest tests/test_auth.py

# Mode verbose
pytest -v

# Arrêter au premier échec
pytest -x
```

### Exemple de test

```python
# tests/test_auth.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "nom": "Delmat",
            "prenom": "leonel",
            "email": "leonel@example.com",
            "telephone": "++237657450314",
            "password": "SecurePass123!"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "leonel@example.com"
    assert "id" in data
```

---

### Intégration notifications dans les services métier

- **MLService** : notification email optionnelle lors d'une prédiction
- **ExpertSystemService** : notification email optionnelle lors d'une réponse
- **AuthService** : notification email automatique à l'inscription

Pour personnaliser ou étendre (WhatsApp, SMS, Telegram), utilisez les méthodes de `NotificationService` dans vos services métier.

---

## 🚀 Déploiement

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'application
COPY . .

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: agropredict
      POSTGRES_PASSWORD: password
      POSTGRES_DB: agropredict
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://agropredict:password@db:5432/agropredict
    depends_on:
      - db

volumes:
  postgres_data:
```

### Lancer avec Docker

```bash
# Build et lancer
docker-compose up --build

# En arrière-plan
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

### Déploiement sur serveur

```bash
# Avec systemd
sudo nano /etc/systemd/system/agropredict.service
```

```ini
[Unit]
Description=AgroPredict API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/agropredict
Environment="PATH=/var/www/agropredict/venv/bin"
ExecStart=/var/www/agropredict/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer
sudo systemctl enable agropredict
sudo systemctl start agropredict
sudo systemctl status agropredict
```

---

## 📝 Scripts utiles

### Initialisation de la base de données

```python
# scripts/init_db.py
from app.database import engine
from app.models.base import Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from sqlalchemy.orm import Session

# Créer toutes les tables
Base.metadata.create_all(bind=engine)

# Créer un admin
with Session(engine) as db:
    admin = User(
        nom="Admin",
        prenom="Super",
        email="admin@agropredict.com",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN,
        telephone="+237600000000"
    )
    db.add(admin)
    db.commit()
    print("✅ Admin créé : admin@agropredict.com")
```

### Seed data

```python
# scripts/seed_data.py
from app.database import SessionLocal
from app.models.culture import Culture, TypeCulture
from app.schemas.culture import BesoinsNutriments

db = SessionLocal()

cultures = [
    Culture(
        nom="Maïs",
        nom_scientifique="Zea mays",
        type_culture=TypeCulture.CEREALES,
        temperature_min=18,
        temperature_max=32,
        temperature_optimale=25,
        precipitation_min=500,
        precipitation_max=800,
        humidite_sol_min=60,
        humidite_sol_max=80,
        sols_compatibles=["limoneux", "argileux"],
        ph_min=5.8,
        ph_max=7.5,
        duree_cycle=120,
        rendement_moyen=5.5
    ),
    # Ajouter d'autres cultures...
]

db.add_all(cultures)
db.commit()
print(f"✅ {len(cultures)} cultures ajoutées")
```

---

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit (`git commit -m 'Ajout nouvelle fonctionnalité'`)
4. Push (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request

---

## 📞 Support

- Email: backend@agropredict.com
- Documentation: https://docs.agropredict.com
- Issues:  https://github.com/Prog-Web-4GI-ENSPY/IOT_SOIL_BACKEND/issues

---

## 📜 Licence

MIT License - Voir [LICENSE](LICENSE)

---

**Made with ❤️ by AgroPredict Team**