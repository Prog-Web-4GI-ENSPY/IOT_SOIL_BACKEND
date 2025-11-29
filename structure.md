IOT_SOIL_BACKEND/
│
├── README.md
├── requirements.txt
├── .env.example
├── alembic.ini
├── main.py
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   │
│   ├── models/
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
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── location.py
│   │   ├── terrain.py
│   │   ├── parcelle.py
│   │   ├── capteur.py
│   │   ├── sensor_data.py
│   │   ├── culture.py
│   │   ├── prediction.py
│   │   ├── recommendation.py
│   │   ├── alert.py
│   │   └── common.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── localites.py
│   │       ├── terrains.py
│   │       ├── parcelles.py
│   │       ├── capteurs.py
│   │       ├── sensor_data.py
│   │       ├── cultures.py
│   │       ├── predictions.py
│   │       └── recommendations.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── chirpstack.py
│   │   ├── prediction.py
│   │   └── recommendation.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   └── config.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── geometry.py
│       └── validators.py
│
├── alembic/
│   ├── versions/
│   └── env.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── api/