from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.location_service import LocaliteService
from app.schemas.location import LocaliteCreate, LocaliteUpdate, LocaliteResponse, Continent, ClimateZone
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/localites",
    tags=["Localités"]
)


@router.post(
    "/",
    response_model=LocaliteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle localité"
)
async def create_localite(
    localite_data: LocaliteCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle localité avec ses informations géographiques et climatiques.

    **Champs requis :**
    - **nom**: Nom de la localité
    - **latitude**: -90 à 90
    - **longitude**: -180 à 180
    - **ville**: Nom de la ville
    - **pays**: Nom du pays
    - **continent**: Continent
    - **timezone**: Fuseau horaire (ex: "Africa/Douala")
    - **superficie**: Superficie en km²

    **Champs optionnels :**
    - **altitude**: Altitude en mètres
    - **quartier**, **region**, **code_postal**: Informations d'adresse
    - **population**: Nombre d'habitants
    - **climate_zone**: Zone climatique
    """
    return LocaliteService.create_localite(db, localite_data, str(current_user.id))


@router.get(
    "/",
    response_model=List[LocaliteResponse],
    summary="Récupérer toutes les localités"
)
async def get_all_localites(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments"),
    continent: Optional[Continent] = Query(None, description="Filtrer par continent"),
    climate_zone: Optional[ClimateZone] = Query(None, description="Filtrer par zone climatique"),
    pays: Optional[str] = Query(None, description="Filtrer par pays"),
    ville: Optional[str] = Query(None, description="Filtrer par ville"),
    search: Optional[str] = Query(None, description="Recherche globale (nom, ville, pays, région)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les localités avec possibilité de filtrage.

    **Filtres disponibles :**
    - **continent**: Filtrer par continent
    - **climate_zone**: Filtrer par zone climatique
    - **pays**: Recherche partielle dans le nom du pays
    - **ville**: Recherche partielle dans le nom de la ville
    - **search**: Recherche globale dans nom, ville, pays et région

    **Pagination :**
    - **skip**: Nombre d'éléments à ignorer
    - **limit**: Nombre maximum d'éléments à retourner (max 1000)
    """
    return LocaliteService.get_all_localites(
        db, skip, limit, continent, climate_zone, pays, ville, search
    )


@router.get(
    "/statistics",
    summary="Statistiques des localités"
)
async def get_localite_statistics(
    db: Session = Depends(get_db)
):
    """
    Obtenir les statistiques globales des localités.

    Retourne :
    - Nombre total de localités
    - Répartition par continent
    - Répartition par zone climatique
    - Superficie totale couverte
    """
    return LocaliteService.get_localite_statistics(db)


@router.get(
    "/countries",
    summary="Liste des pays disponibles"
)
async def get_countries_list(
    db: Session = Depends(get_db)
):
    """
    Obtenir la liste de tous les pays avec le nombre de localités par pays.

    Utile pour remplir des listes déroulantes ou filtres.
    """
    return LocaliteService.get_countries_list(db)




@router.get(
    "/country/{pays}",
    response_model=List[LocaliteResponse],
    summary="Localités par pays"
)
async def get_localites_by_country(
    pays: str,
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les localités d'un pays spécifique.

    Les résultats sont triés par nom de ville.
    """
    return LocaliteService.get_localites_by_country(db, pays)


@router.get(
    "/{localite_id}",
    response_model=LocaliteResponse,
    summary="Récupérer une localité par son ID"
)
async def get_localite(
    localite_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupérer les détails complets d'une localité spécifique.
    """
    return LocaliteService.get_localite_by_id(db, localite_id)


@router.put(
    "/{localite_id}",
    response_model=LocaliteResponse,
    summary="Mettre à jour une localité"
)
async def update_localite(
    localite_id: str,
    localite_data: LocaliteUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour les informations d'une localité.

    Seuls les champs fournis seront mis à jour.
    Les coordonnées GPS ne peuvent pas être modifiées après création.
    """
    return LocaliteService.update_localite(db, localite_id, localite_data)


@router.delete(
    "/{localite_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer une localité"
)
async def delete_localite(
    localite_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une localité (suppression logique).

    La suppression échouera si des terrains sont associés à cette localité.
    Vous devez d'abord supprimer ou réassigner les terrains.
    """
    return LocaliteService.delete_localite(db, localite_id)
