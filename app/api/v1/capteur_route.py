from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db

# Importez les schémas, le service et le modèle
from app.schemas.capteur import Capteur as CapteurSchema, CapteurCreate, CapteurUpdate
from app.services.capteur_service import capteur_service
from app.models.capteur import Capteur

router = APIRouter()

# --- 1. Création (POST) ---
@router.post(
    "/",
    response_model=CapteurSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau capteur"
)
def create_capteur(
    *,
    db: Session = Depends(get_db),
    capteur_in: CapteurCreate,
) -> Any:
    """
    Crée un capteur. Nécessite `nom`, `dev_eui`, `parcelle_id` et `date_installation`.
    """
    try:
        capteur = capteur_service.create_capteur(db, capteur_data=capteur_in)
        return capteur
    except ValueError as e:
        # Gère l'erreur de DevEUI déjà existant, levée par le service CRUD
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=str(e)
        )

# --- 2. Lecture Multiples (GET /) ---
@router.get(
    "/",
    response_model=List[CapteurSchema],
    summary="Lister tous les capteurs"
)
def read_capteurs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Récupère une liste paginée de tous les capteurs.
    """
    capteurs = capteur_service.get_capteurs(db, skip=skip, limit=limit)
    return capteurs

# --- 3. Lecture Simple (GET /{id}) ---
@router.get(
    "/{capteur_id}",
    response_model=CapteurSchema,
    summary="Lire un capteur par ID"
)
def read_capteur(
    capteur_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupère un capteur spécifique par son UUID.
    """
    capteur = capteur_service.get_capteur(db, capteur_id=capteur_id)
    if not capteur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Capteur non trouvé"
        )
    return capteur

# --- 4. Mise à Jour (PUT/PATCH /{id}) ---
@router.put(
    "/{capteur_id}",
    response_model=CapteurSchema,
    summary="Mettre à jour un capteur existant"
)
def update_capteur(
    *,
    db: Session = Depends(get_db),
    capteur_id: str,
    capteur_in: CapteurUpdate
) -> Any:
    """
    Met à jour un capteur par son UUID.
    """
    capteur = capteur_service.get_capteur(db, capteur_id=capteur_id)
    if not capteur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Capteur non trouvé"
        )
    
    try:
        capteur = capteur_service.update_capteur(db, capteur_id=capteur.id, capteur_data=capteur_in)
        return capteur
    except ValueError as e:
        # Gère l'erreur de DevEUI en conflit lors de la mise à jour
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=str(e)
        )


# --- 5. Suppression (DELETE /{id}) ---
@router.delete(
    "/{capteur_id}",
    response_model=CapteurSchema,
    summary="Supprimer un capteur"
)
def delete_capteur(
    capteur_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Supprime un capteur par son UUID.
    """
    try:
        capteur = capteur_service.delete_capteur(db, capteur_id=capteur_id)
        return capteur
    except ValueError as e:
        # Gère l'erreur si le capteur n'existe pas
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )

    # --- 6. Lecture par Code (GET /code/{code}) ---
@router.get(
    "/code/{code}",
    response_model=CapteurSchema,
    summary="Récupérer un capteur par son code"
)
def read_capteur_by_code(
    code: str,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user) # Si vous utilisez l'authentification
) -> Any:
    """
    Récupère les détails d'un capteur spécifique en utilisant son code unique.
    """
    # Si vous avez l'user_id, passez-le : capteur_service.get_capteur_by_code(db, code, str(current_user.id))
    capteur = capteur_service.get_capteur_by_code(db, code=code)
    return capteur