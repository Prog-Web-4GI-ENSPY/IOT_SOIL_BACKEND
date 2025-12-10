from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationCreate, RecommendationUpdate
from datetime import datetime
import uuid


class RecommendationService:
    """Service pour la gestion des recommandations agricoles"""
    
    @staticmethod
    def create_recommendation(
        db: Session, 
        recommendation_data: RecommendationCreate,
        user_id: str
    ) -> Recommendation:
        """Créer une nouvelle recommandation"""
        # Vérifier que la parcelle appartient à l'utilisateur
        from app.models.parcelle import Parcelle
        from app.models.terrain import Terrain

        parcelle = db.query(Parcelle).join(Terrain).filter(
            Parcelle.id == recommendation_data.parcelle_id,
            Terrain.user_id == user_id,
            Parcelle.deleted_at.is_(None)
        ).first()
        
        if not parcelle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parcelle non trouvée ou accès refusé"
            )
        
        try:
            recommendation = Recommendation(
                id=str(uuid.uuid4()),
                titre=recommendation_data.titre,
                contenu=recommendation_data.description,
                priorite=getattr(recommendation_data, 'priorite', 'Normal'),
                parcelle_id=recommendation_data.parcelle_id,
                date_emission=recommendation_data.date_creation or datetime.utcnow()
            )
            
            db.add(recommendation)
            db.commit()
            db.refresh(recommendation)
            return recommendation
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création de la recommandation: {str(e)}"
            )
    
    @staticmethod
    def get_recommendation_by_id(
        db: Session, 
        recommendation_id: str, 
        user_id: str
    ) -> Recommendation:
        """Récupérer une recommandation par son ID"""
        from app.models.parcelle import Parcelle
        from app.models.terrain import Terrain

        recommendation = db.query(Recommendation).join(
            Parcelle, Recommendation.parcelle_id == Parcelle.id
        ).join(
            Terrain, Parcelle.terrain_id == Terrain.id
        ).filter(
            Recommendation.id == recommendation_id,
            Terrain.user_id == user_id,
            Recommendation.deleted_at.is_(None)
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recommandation non trouvée"
            )
        
        return recommendation
    
    @staticmethod
    def get_recommendations_by_parcelle(
        db: Session, 
        parcelle_id: str, 
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        priorite: Optional[str] = None
    ) -> List[Recommendation]:
        """Récupérer toutes les recommandations d'une parcelle"""
        from app.models.parcelle import Parcelle
        from app.models.terrain import Terrain

        # Vérifier que la parcelle appartient à l'utilisateur
        parcelle = db.query(Parcelle).join(Terrain).filter(
            Parcelle.id == parcelle_id,
            Terrain.user_id == user_id,
            Parcelle.deleted_at.is_(None)
        ).first()
        
        if not parcelle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parcelle non trouvée"
            )
        
        query = db.query(Recommendation).filter(
            Recommendation.parcelle_id == parcelle_id,
            Recommendation.deleted_at.is_(None)
        )
        
        if priorite:
            query = query.filter(Recommendation.priorite == priorite)
        
        return query.order_by(
            Recommendation.date_emission.desc()
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_all_recommendations(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        priorite: Optional[str] = None
    ) -> List[Recommendation]:
        """Récupérer toutes les recommandations de l'utilisateur"""
        from app.models.parcelle import Parcelle
        from app.models.terrain import Terrain

        query = db.query(Recommendation).join(
            Parcelle, Recommendation.parcelle_id == Parcelle.id
        ).join(
            Terrain, Parcelle.terrain_id == Terrain.id
        ).filter(
            Terrain.user_id == user_id,
            Recommendation.deleted_at.is_(None)
        )
        
        if priorite:
            query = query.filter(Recommendation.priorite == priorite)
        
        return query.order_by(
            Recommendation.date_emission.desc()
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_recommendation(
        db: Session, 
        recommendation_id: str, 
        recommendation_data: RecommendationUpdate,
        user_id: str
    ) -> Recommendation:
        """Mettre à jour une recommandation"""
        recommendation = RecommendationService.get_recommendation_by_id(
            db, recommendation_id, user_id
        )
        
        update_data = recommendation_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == 'description':
                setattr(recommendation, 'contenu', value)
            elif field == 'date_creation':
                setattr(recommendation, 'date_emission', value)
            else:
                setattr(recommendation, field, value)
        
        try:
            db.commit()
            db.refresh(recommendation)
            return recommendation
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la mise à jour: {str(e)}"
            )
    
    @staticmethod
    def delete_recommendation(
        db: Session, 
        recommendation_id: str, 
        user_id: str
    ) -> dict:
        """Supprimer une recommandation (soft delete)"""
        recommendation = RecommendationService.get_recommendation_by_id(
            db, recommendation_id, user_id
        )
        
        try:
            recommendation.soft_delete()
            db.commit()
            return {"message": "Recommandation supprimée avec succès"}
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la suppression: {str(e)}"
            )
    
    @staticmethod
    def generate_weather_based_recommendation(
        db: Session,
        parcelle_id: str,
        user_id: str,
        weather_data: dict
    ) -> Recommendation:
        """Générer une recommandation basée sur les données météo"""
        from app.models.parcelle import Parcelle
        from app.models.terrain import Terrain

        # Vérifier que la parcelle appartient à l'utilisateur
        parcelle = db.query(Parcelle).join(Terrain).filter(
            Parcelle.id == parcelle_id,
            Terrain.user_id == user_id,
            Parcelle.deleted_at.is_(None)
        ).first()
        
        if not parcelle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parcelle non trouvée"
            )
        
        # Analyser les données météo et générer une recommandation
        titre, contenu, priorite = RecommendationService._analyze_weather(
            weather_data, parcelle
        )
        
        try:
            recommendation = Recommendation(
                id=str(uuid.uuid4()),
                titre=titre,
                contenu=contenu,
                priorite=priorite,
                parcelle_id=parcelle_id,
                date_emission=datetime.utcnow()
            )
            
            db.add(recommendation)
            db.commit()
            db.refresh(recommendation)
            return recommendation
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la génération: {str(e)}"
            )
    
    @staticmethod
    def _analyze_weather(weather_data: dict, parcelle) -> tuple:
        """Analyser les données météo et générer des recommandations"""
        temperature = weather_data.get('temperature', 25)
        humidity = weather_data.get('humidity', 60)
        precipitation = weather_data.get('precipitation', 0)
        
        # Logique de recommandation basée sur la météo
        if precipitation > 50:
            return (
                "Attention: Fortes précipitations prévues",
                f"Des précipitations importantes ({precipitation}mm) sont prévues. "
                "Vérifiez le drainage de votre parcelle et reportez les activités "
                "de plantation ou de récolte si possible.",
                "Urgent"
            )
        elif temperature > 35:
            return (
                "Alerte: Températures élevées",
                f"Températures élevées prévues ({temperature}°C). "
                "Assurez-vous que votre système d'irrigation fonctionne correctement. "
                "Envisagez d'augmenter la fréquence d'arrosage.",
                "Urgent"
            )
        elif humidity < 30:
            return (
                "Attention: Faible humidité",
                f"L'humidité est faible ({humidity}%). "
                "Surveillez l'état de vos cultures et augmentez l'irrigation si nécessaire.",
                "Normal"
            )
        elif temperature < 10:
            return (
                "Alerte: Risque de gel",
                f"Températures basses prévues ({temperature}°C). "
                "Protégez vos cultures sensibles au froid. "
                "Envisagez des mesures de protection contre le gel.",
                "Urgent"
            )
        else:
            return (
                "Conditions météo favorables",
                f"Les conditions météorologiques sont favorables pour les activités agricoles. "
                f"Température: {temperature}°C, Humidité: {humidity}%.",
                "Faible"
            )