from fastapi import APIRouter
from app.api.v1 import capteur_route 
from app.routers import auth_router, users_router

# Définissez le routeur principal qui sera importé dans main.py
api_router = APIRouter()

# CRUD Capteurs endpoints
api_router.include_router(
    capteur_route.router, 
    prefix="/capteurs", 
    tags=["Capteurs"]
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
