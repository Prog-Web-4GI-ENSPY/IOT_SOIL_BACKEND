from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.culture import Culture
from app.schemas.culture import CultureCreate, CultureUpdate, Culture as CultureResponse
from app.core.dependencies import get_current_user
from app.models.user import User
from fastapi import HTTPException
import uuid

router = APIRouter(
    prefix="/cultures",
    tags=["Cultures"]
)


@router.post(
    "/",
    response_model=CultureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle culture"
)
async def create_culture(
    culture_data: CultureCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle culture agricole.

    - **nom**: Nom de la culture (obligatoire, unique)
    - **description**: Description de la culture
    - **type_culture**: Type de culture (ex: Céréale, Légumineuse, Racine)
    """
    # Vérifier si une culture avec le même nom existe déjà
    existing = db.query(Culture).filter(Culture.nom == culture_data.nom).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Une culture avec le nom '{culture_data.nom}' existe déjà"
        )

    culture = Culture(
        id=str(uuid.uuid4()),
        nom=culture_data.nom,
        description=culture_data.description,
        type_culture=culture_data.type_culture
    )

    db.add(culture)
    db.commit()
    db.refresh(culture)
    return culture


@router.get(
    "/",
    response_model=List[CultureResponse],
    summary="Récupérer toutes les cultures"
)
async def get_all_cultures(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments"),
    type_culture: Optional[str] = Query(None, description="Filtrer par type de culture"),
    search: Optional[str] = Query(None, description="Rechercher dans le nom ou description"),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les cultures.

    Possibilité de filtrer par type et rechercher par nom ou description.
    """
    query = db.query(Culture)

    if type_culture:
        query = query.filter(Culture.type_culture.ilike(f"%{type_culture}%"))

    if search:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Culture.nom.ilike(f"%{search}%"),
                Culture.description.ilike(f"%{search}%")
            )
        )

    query = query.order_by(Culture.nom)
    return query.offset(skip).limit(limit).all()


@router.get(
    "/{culture_id}",
    response_model=CultureResponse,
    summary="Récupérer une culture par son ID"
)
async def get_culture(
    culture_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails d'une culture spécifique.
    """
    culture = db.query(Culture).filter(Culture.id == culture_id).first()

    if not culture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Culture non trouvée"
        )

    return culture


@router.get(
    "/nom/{nom}",
    response_model=CultureResponse,
    summary="Récupérer une culture par son nom"
)
async def get_culture_by_name(
    nom: str,
    db: Session = Depends(get_db)
):
    """
    Récupérer une culture par son nom.
    """
    culture = db.query(Culture).filter(Culture.nom.ilike(nom)).first()

    if not culture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Culture '{nom}' non trouvée"
        )

    return culture


@router.put(
    "/{culture_id}",
    response_model=CultureResponse,
    summary="Mettre à jour une culture"
)
async def update_culture(
    culture_id: str,
    culture_data: CultureUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour une culture.

    Seuls les champs fournis seront mis à jour.
    """
    culture = db.query(Culture).filter(Culture.id == culture_id).first()

    if not culture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Culture non trouvée"
        )

    # Vérifier si le nouveau nom existe déjà
    if culture_data.nom and culture_data.nom != culture.nom:
        existing = db.query(Culture).filter(Culture.nom == culture_data.nom).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une culture avec le nom '{culture_data.nom}' existe déjà"
            )

    update_data = culture_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(culture, field, value)

    db.commit()
    db.refresh(culture)
    return culture


@router.delete(
    "/{culture_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une culture"
)
async def delete_culture(
    culture_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une culture.

    Note: La suppression échouera si des parcelles utilisent cette culture.
    """
    culture = db.query(Culture).filter(Culture.id == culture_id).first()

    if not culture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Culture non trouvée"
        )

    try:
        db.delete(culture)
        db.commit()
        return {"message": "Culture supprimée avec succès"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer la culture: {str(e)}"
        )


@router.get(
    "/statistics/summary",
    summary="Statistiques des cultures"
)
async def get_culture_statistics(
    db: Session = Depends(get_db)
):
    """
    Obtenir les statistiques des cultures.

    Retourne le nombre de cultures par type.
    """
    from sqlalchemy import func

    # Total des cultures
    total = db.query(func.count(Culture.id)).scalar()

    # Par type
    by_type = db.query(
        Culture.type_culture,
        func.count(Culture.id).label('count')
    ).group_by(Culture.type_culture).all()

    type_stats = {type_culture or "Non défini": count for type_culture, count in by_type}

    return {
        "total": total,
        "by_type": type_stats
    }


@router.get(
    "/types/list",
    summary="Liste des types de cultures"
)
async def get_culture_types(
    db: Session = Depends(get_db)
):
    """
    Obtenir la liste unique de tous les types de cultures.

    Utile pour remplir des listes déroulantes.
    """
    types = db.query(Culture.type_culture).distinct().filter(
        Culture.type_culture.isnot(None)
    ).all()

    return {
        "types": [t[0] for t in types if t[0]]
    }
