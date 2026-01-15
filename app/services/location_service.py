from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from fastapi import HTTPException, status
import uuid
from app.models.location import Localite, Continent, ClimateZone
from app.schemas.location import LocaliteCreate, LocaliteUpdate


class LocaliteService:
    """Service pour la gestion des localités"""

    @staticmethod
    def create_localite(db: Session, localite_data: LocaliteCreate, user_id: str) -> Localite:
        """Créer une nouvelle localité"""
        try:
            # Créer la localité sans vérification de coordonnées (supprimées)


            localite = Localite(
                id=str(uuid.uuid4()),
                nom=localite_data.nom,
                quartier=localite_data.quartier,
                ville=localite_data.ville,
                region=localite_data.region,
                pays=localite_data.pays,
                code_postal=localite_data.code_postal,
                continent=localite_data.continent,
                timezone=localite_data.timezone,
                superficie=localite_data.superficie,
                population=localite_data.population,
                climate_zone=localite_data.climate_zone
            )


            db.add(localite)
            db.commit()
            db.refresh(localite)
            return localite

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création de la localité: {str(e)}"
            )

    @staticmethod
    def get_localite_by_id(db: Session, localite_id: str) -> Localite:
        """Récupérer une localité par son ID"""
        localite = db.query(Localite).filter(
            Localite.id == localite_id,
            Localite.deleted_at.is_(None)
        ).first()

        if not localite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Localité non trouvée"
            )

        return localite

    @staticmethod
    def get_all_localites(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        continent: Optional[Continent] = None,
        climate_zone: Optional[ClimateZone] = None,
        pays: Optional[str] = None,
        ville: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Localite]:
        """Récupérer toutes les localités avec filtres"""
        query = db.query(Localite).filter(Localite.deleted_at.is_(None))

        # Filtres
        if continent:
            query = query.filter(Localite.continent == continent)

        if climate_zone:
            query = query.filter(Localite.climate_zone == climate_zone)

        if pays:
            query = query.filter(Localite.pays.ilike(f"%{pays}%"))

        if ville:
            query = query.filter(Localite.ville.ilike(f"%{ville}%"))

        if search:
            query = query.filter(
                or_(
                    Localite.nom.ilike(f"%{search}%"),
                    Localite.ville.ilike(f"%{search}%"),
                    Localite.pays.ilike(f"%{search}%"),
                    Localite.region.ilike(f"%{search}%")
                )
            )

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_localite(
        db: Session,
        localite_id: str,
        localite_data: LocaliteUpdate
    ) -> Localite:
        """Mettre à jour une localité"""
        localite = LocaliteService.get_localite_by_id(db, localite_id)

        update_data = localite_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(localite, field, value)

        try:
            db.commit()
            db.refresh(localite)
            return localite
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la mise à jour: {str(e)}"
            )

    @staticmethod
    def delete_localite(db: Session, localite_id: str) -> dict:
        """Supprimer une localité (soft delete)"""
        localite = LocaliteService.get_localite_by_id(db, localite_id)

        # Vérifier qu'aucun terrain n'est associé
        if localite.terrains:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossible de supprimer: {len(localite.terrains)} terrain(s) associé(s)"
            )

        try:
            localite.soft_delete()
            db.commit()
            return {"message": "Localité supprimée avec succès"}
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la suppression: {str(e)}"
            )


    @staticmethod
    def get_localite_statistics(db: Session) -> dict:
        """Obtenir les statistiques des localités"""
        stats = {
            "total": db.query(func.count(Localite.id)).filter(
                Localite.deleted_at.is_(None)
            ).scalar(),
            "by_continent": {},
            "by_climate_zone": {},
            "superficie_totale": 0,
            "population_totale": 0
        }

        # Statistiques par continent
        continent_stats = db.query(
            Localite.continent,
            func.count(Localite.id).label('count')
        ).filter(
            Localite.deleted_at.is_(None)
        ).group_by(Localite.continent).all()

        for continent, count in continent_stats:
            stats["by_continent"][continent.value if continent else "Non défini"] = count

        # Statistiques par zone climatique
        climate_stats = db.query(
            Localite.climate_zone,
            func.count(Localite.id).label('count')
        ).filter(
            Localite.deleted_at.is_(None)
        ).group_by(Localite.climate_zone).all()

        for climate, count in climate_stats:
            stats["by_climate_zone"][climate.value if climate else "Non défini"] = count

        # Superficie et population totales
        totals = db.query(
            func.sum(Localite.superficie).label('superficie'),
            func.sum(Localite.population).label('population')
        ).filter(Localite.deleted_at.is_(None)).first()

        stats["superficie_totale"] = float(totals.superficie or 0)
        stats["population_totale"] = int(totals.population or 0)

        return stats

    @staticmethod
    def get_localites_by_country(db: Session, pays: str) -> List[Localite]:
        """Récupérer toutes les localités d'un pays"""
        return db.query(Localite).filter(
            Localite.pays.ilike(f"%{pays}%"),
            Localite.deleted_at.is_(None)
        ).order_by(Localite.ville).all()

    @staticmethod
    def get_countries_list(db: Session) -> List[dict]:
        """Obtenir la liste des pays disponibles"""
        countries = db.query(
            Localite.pays,
            Localite.continent,
            func.count(Localite.id).label('count')
        ).filter(
            Localite.deleted_at.is_(None)
        ).group_by(Localite.pays, Localite.continent).all()

        return [
            {
                "pays": country.pays,
                "continent": country.continent.value if country.continent else None,
                "nombre_localites": country.count
            }
            for country in countries
        ]
