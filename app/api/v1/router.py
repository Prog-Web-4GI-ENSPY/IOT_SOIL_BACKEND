from fastapi import APIRouter

# Importez tous vos routeurs spécifiques

# Définissez le routeur principal qui sera importé dans main.py
api_router = APIRouter()

# Incluez vos sous-routeurs
# Note : Ici, nous utilisons un chemin vide car le préfixe sera géré dans main.py
#api_router.include_router(parcelles.router, tags=["Parcelles"]) 

# Ajoutez d'autres routeurs ici :
# api_router.include_router(users.router, tags=["Users"])
# api_router.include_router(cultures.router, tags=["Cultures"])
