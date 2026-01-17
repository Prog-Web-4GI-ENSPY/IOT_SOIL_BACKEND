from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db

# Importez les schémas, le service et le modèle
from app.schemas.capteur import Capteur as CapteurSchema, CapteurCreate, CapteurUpdate
from app.services.capteur_service import capteur_service
from app.services.capteur_parcelle_service import assign_capteur_to_parcelle, desassign_capteur_de_parcelle
from app.models.capteur import Capteur
from app.core.dependencies import require_admin, get_current_user

router = APIRouter()

# --- 1. Création (POST) ---
@router.post(
    "/",
    response_model=CapteurSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau capteur (Admin uniquement)"
)
def create_capteur(
    *,
    db: Session = Depends(get_db),
    capteur_in: CapteurCreate,
    current_user=Depends(require_admin)
) -> Any:
    """
    Crée un capteur. Réservé aux administrateurs.
    """
    try:
        capteur = capteur_service.create_capteur(db, capteur_data=capteur_in)
        return capteur
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=str(e)
        )

# --- 2. Lecture Multiples (GET /) ---
@router.get(
    "/",
    response_model=List[CapteurSchema],
    summary="Lister tous les capteurs (Admin uniquement)"
)
def read_capteurs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(require_admin)
) -> Any:
    """
    Récupère une liste complète de tous les capteurs. Réservé aux administrateurs.
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
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
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
    summary="Mettre à jour un capteur existant (Admin uniquement)"
)
def update_capteur(
    *,
    db: Session = Depends(get_db),
    capteur_id: str,
    capteur_in: CapteurUpdate,
    current_user=Depends(require_admin)
) -> Any:
    """
    Met à jour un capteur. Réservé aux administrateurs.
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=str(e)
        )


# --- 5. Suppression (DELETE /{id}) ---
@router.delete(
    "/{capteur_id}",
    response_model=CapteurSchema,
    summary="Supprimer un capteur (Admin uniquement)"
)
def delete_capteur(
    capteur_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
) -> Any:
    """
    Supprime un capteur. Réservé aux administrateurs.
    """
    try:
        capteur = capteur_service.delete_capteur(db, capteur_id=capteur_id)
        return capteur
    except ValueError as e:
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
    current_user=Depends(get_current_user)
) -> Any:
    """
    Récupère les détails d'un capteur spécifique en utilisant son code unique.
    """
    capteur = capteur_service.get_capteur_by_code(db, code=code)
    if not capteur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Capteur non trouvé"
        )
    return capteur

# --- 7. Assignation/Désassignation ---

@router.post(
    "/assign",
    summary="Assigner un capteur à une parcelle"
)
def assign_capteur(
    code_parcelle: str,
    code_capteur: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
) -> Any:
    """
    Assigne un capteur à une parcelle. Accessible à tous les utilisateurs connectés.
    """
    return assign_capteur_to_parcelle(db, code_parcelle, code_capteur)

@router.post(
    "/desassign",
    summary="Désassigner un capteur d'une parcelle"
)
def desassign_capteur(
    code_parcelle: str,
    code_capteur: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
) -> Any:
    """
    Désassigne un capteur d'une parcelle. Accessible à tous les utilisateurs connectés.
    """
    return desassign_capteur_de_parcelle(db, code_parcelle, code_capteur)