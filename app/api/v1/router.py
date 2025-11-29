from fastapi import APIRouter
from app.api.v1 import capteur_route
# Importez tous vos routeurs spécifiques

# Définissez le routeur principal qui sera importé dans main.py
api_router = APIRouter()

# Incluez vos sous-routeurs
api_router.include_router(capteur_route.router prefix="/capteurs", tags=["Capteurs"])