from fastapi import APIRouter
from app.api.v1 import (
    capteur_route,
    parcelle_router,
    terrain_router,
    recommendation_router,
    location_router,
    sensor_data_router,
    chirpstack_router
)
from app.routers import auth_router, users_router

# Définissez le routeur principal qui sera importé dans main.py
api_router = APIRouter()

# ============================================================================
# GESTION DES UTILISATEURS ET AUTHENTIFICATION
# ============================================================================

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

# ============================================================================
# GESTION DES ENTITÉS AGRICOLES
# ============================================================================

# Localités endpoints
api_router.include_router(
    location_router.router,
    prefix="/localites",
    tags=["Localités"]
)

# Terrains endpoints
api_router.include_router(
    terrain_router.router,
    prefix="/terrains",
    tags=["Terrains"]
)

# Parcelles endpoints
api_router.include_router(
    parcelle_router.router,
    prefix="/parcelles",
    tags=["Parcelles"]
)

# ============================================================================
# GESTION DES CAPTEURS ET DONNÉES
# ============================================================================

# CRUD Capteurs endpoints
api_router.include_router(
    capteur_route.router,
    prefix="/capteurs",
    tags=["Capteurs"]
)

# Sensor Data endpoints
api_router.include_router(
    sensor_data_router.router,
    prefix="/sensor-data",
    tags=["Données de Capteurs"]
)

# ============================================================================
# INTÉGRATION CHIRPSTACK
# ============================================================================

# ChirpStack webhooks et communication
api_router.include_router(
    chirpstack_router.router,
    prefix="/chirpstack",
    tags=["ChirpStack"]
)

# Recommendations endpoints
api_router.include_router(
    recommendation_router.router,
    prefix="/recommendations",
    tags=["Recommandations"]
)
