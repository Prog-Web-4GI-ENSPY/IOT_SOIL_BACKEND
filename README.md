# 🌾 AgroPredict-Backend

## 🌟 Aperçu du Projet

**AgroPredict-Backend** est le cerveau d'une solution d'agriculture intelligente (Smart Farming) conçue pour optimiser le rendement des cultures. Il s'agit d'une **API RESTful** puissante et évolutive, construite pour collecter des données de capteurs IoT, exécuter des modèles de prédiction agronomique (rendement, risques), et générer des recommandations d'actions précises pour les agriculteurs.

Ce projet a été réalisé dans le cadre de l'**Unité d'Enseignement (UE) Électronique et Interfaçage** en 4ème année de Génie Informatique à l'**École Nationale Supérieure Polytechnique de Yaoundé (ENSPY)**.

### 🎯 Objectifs Clés

  * **Intégration IoT :** Recevoir et traiter les données en temps réel provenant des capteurs de sol et environnementaux (via des systèmes comme ChirpStack/LoRaWAN).
  * **Modélisation Agronomique :** Fournir des *endpoints* pour des **prédictions** basées sur des modèles d'apprentissage automatique (ML) intégrant les données de capteurs et les informations de parcelle.
  * **Système de Recommandation :** Générer des **recommandations** d'irrigation, de fertilisation ou de gestion des maladies.
  * **Base de Données Robuste :** Gérer les utilisateurs, les terrains, les parcelles, les capteurs, et toutes les données historiques.

-----

## 🛠️ Stack Technique

| Catégorie | Outil / Librairie | Description |
| :--- | :--- | :--- |
| **Framework Web** | **FastAPI** | Construction rapide et performante des API avec typage Python standard (Pydantic). |
| **Base de Données** | **PostgreSQL** (recommandé) | Base de données relationnelle robuste et adaptée aux applications complexes. |
| **ORM** | **SQLAlchemy** | Mappage Objet-Relationnel pour interagir avec la base de données de manière orientée objet. |
| **Migrations** | **Alembic** | Gestion des migrations de schémas de base de données. |
| **Configuration** | **Pydantic Settings** | Gestion des variables d'environnement. |
| **Services Externes** | **ChirpStack (Simulé/Intégré)** | Service pour l'interfaçage avec le réseau LoRaWAN/IoT. |

-----

## 🚀 Démarrage Rapide

Ces instructions vous permettront d'obtenir une copie opérationnelle du projet sur votre machine locale à des fins de développement et de test.

### Prérequis

  * **Python 3.8+**
  * **pip** (gestionnaire de paquets Python)
  * **PostgreSQL** (ou autre base de données supportée par SQLAlchemy, configurée localement ou via Docker)

### 1\. Cloner le Référentiel

```bash
git clone https://github.com/Prog-Web-4GI-ENSPY/IOT_SOIL_BACKEND.git
cd IOT_SOIL_BACKEND
```

### 2\. Créer et Activer l'Environnement Virtuel

Il est crucial d'utiliser un environnement virtuel pour isoler les dépendances.

```bash
python -m venv .venv
source .venv/bin/activate  # Sous Linux/macOS
# .venv\Scripts\activate.bat  # Sous Windows
```

### 3\. Installer les Dépendances

Installez toutes les bibliothèques requises, y compris Alembic et FastAPI.

```bash
pip install -r requirements.txt
```

### 4\. Configuration de l'Environnement

Créez un fichier `.env` à la racine du projet en copiant le fichier d'exemple fourni et en remplissant les valeurs :

```bash
cp .env.example .env
```

**Exemple de `.env` (à adapter) :**

```env
# Database Settings
POSTGRES_USER=agropredict_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agropredict_db
DATABASE_URL=postgresql://agropredict_user:your_secure_password@localhost:5432/agropredict_db

# Security
SECRET_KEY="your-fastapi-secret-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5\. Initialiser la Base de Données et les Migrations

Appliquez les migrations de schéma à la base de données.

```bash
# Vérifier la connexion et mettre à jour la base de données
alembic upgrade head
```

### 6\. Lancer le Serveur

Démarrez le serveur avec Uvicorn :

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Le backend sera accessible à `http://localhost:8000`.

-----

## 🧭 Documentation de l'API

Une fois le serveur lancé, vous pouvez accéder aux documentations interactives :

  * **Swagger UI (Documentation complète) :** `http://localhost:8000/docs`
  * **ReDoc (Vue simplifiée) :** `http://localhost:8000/redoc`

-----

## 📂 Structure des Dossiers

Le projet suit une architecture modulaire et bien organisée :

```
agropredict-backend/
├── app/
│   ├── api/         # Endpoints de l'API (FastAPI Routers)
│   │   ├── v1/      # Versionnement de l'API
│   ├── core/        # Paramètres de configuration (ENV) et sécurité (JWT)
│   ├── models/      # Modèles de base de données (SQLAlchemy)
│   ├── schemas/     # Schémas de données (Pydantic pour validation et sérialisation)
│   ├── services/    # Logique métier et interaction avec services externes (ChirpStack, ML)
│   ├── database.py  # Configuration de la session DB
│   └── ...
├── alembic/         # Fichiers de configuration et versions de migration
├── tests/           # Tests unitaires et d'intégration
└── main.py          # Point d'entrée de l'application FastAPI
```

-----

## 👥 Contributeurs

Ce projet a été réalisé par :

| Nom | Rôle |
| :--- | :--- |
| **[Votre Nom / Nom du Groupe]** | Développeur Backend Principal |
| **[Nom de l'étudiant 2]** | (Ex: Modélisation ML, Infrastructure) |
| **[Nom de l'étudiant 3]** | (Ex: Interfaçage IoT) |

-----

## 🎓 Contexte Académique

  * **Institution :** École Nationale Supérieure Polytechnique de Yaoundé (ENSPY)
  * **Niveau :** 4ème Année, Génie Informatique (GI4)
  * **UE :** Électronique et Interfaçage
  * **Année Académique :** 2024/2025 (Exemple)

-----

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier `LICENSE` pour plus de détails (si applicable).