from fastapi import APIRouter
from app.api.v1 import (
    capteur_route,
    parcelle_router,
    terrain_router,
    recommendation_router,
    location_router,
    alert_router,
    sensor_data_router,
    prediction_router,
    culture_router,
    webhook_router
)
from app.routers import auth_router, users_router

# Définissez le routeur principal qui sera importé dans main.py
api_router = APIRouter()

# CRUD Capteurs endpoints
api_router.include_router(
    capteur_route.router,
    prefix="/capteurs",
    tags=["Capteurs"]
)

# Parcelles endpoints
api_router.include_router(
    parcelle_router.router,
    prefix="/parcelles",
    tags=["Parcelles"]
)

# Terrains endpoints
api_router.include_router(
    terrain_router.router,
    prefix="/terrains",
    tags=["Terrains"]
)

# Recommendations endpoints
api_router.include_router(
    recommendation_router.router,
    prefix="/recommendations",
    tags=["Recommandations"]
)

# Localités endpoints
api_router.include_router(
    location_router.router,
    prefix="/localites",
    tags=["Localités"]
)

# Alertes endpoints
api_router.include_router(
    alert_router.router,
    prefix="/alerts",
    tags=["Alertes"]
)

# Sensor Data endpoints
api_router.include_router(
    sensor_data_router.router,
    prefix="/sensor-data",
    tags=["Données de Capteurs"]
)

# Predictions endpoints
api_router.include_router(
    prediction_router.router,
    prefix="/predictions",
    tags=["Prédictions"]
)

# Cultures endpoints
api_router.include_router(
    culture_router.router,
    prefix="/cultures",
    tags=["Cultures"]
)

# Authentication endpoints
api_router.include_router(
    auth_router.router,
    prefix="/auth",
    tags=["Authentication"]
)

# User management endpoints
api_router.include_router(
    users_router.router,
    prefix="/users",
    tags=["Users"]
)

# Webhooks & Integration endpoints
api_router.include_router(
    webhook_router.router,
    prefix="/webhooks",
    tags=["Webhooks & Intégration"]
)
