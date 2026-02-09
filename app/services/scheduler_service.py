import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User, RecommendationFrequency
from app.models.recommendation import Recommendation
from app.api.v1.recommendation_router import predict_parcelle_crop
from app.models.sensor_data import SensorMeasurements
from sqlalchemy import func

logger = logging.getLogger(__name__)

class SchedulerService:
    """Service pour gérer les tâches périodiques."""
    
    _instance = None
    _running = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SchedulerService, cls).__new__(cls)
        return cls._instance

    async def start(self):
        """Démarre la boucle de vérification périodique."""
        if self._running:
            return
        
        self._running = True
        logger.info("Scheduler Service démarré.")
        
        while self._running:
            try:
                await self.check_and_trigger_recommendations()
            except Exception as e:
                logger.error(f"Erreur dans le scheduler: {str(e)}")
            
            # Vérification toutes les heures (3600 secondes)
            # Pour le dev/test, on pourrait mettre moins.
            await asyncio.sleep(3600)

    def stop(self):
        self._running = False
        logger.info("Scheduler Service arrêté.")

    async def check_and_trigger_recommendations(self):
        """Vérifie quels utilisateurs ont besoin d'une nouvelle recommandation."""
        db = SessionLocal()
        try:
            # Récupérer les utilisateurs avec recommandation activée
            users = db.query(User).filter(User.recommendation_frequency != RecommendationFrequency.DISABLED).all()
            
            for user in users:
                await self.process_user_recommendations(db, user)
                
        finally:
            db.close()

    async def process_user_recommendations(self, db: Session, user: User):
        """Traite les recommandations pour un utilisateur donné."""
        frequency_map = {
            RecommendationFrequency.WEEKLY: 7,
            RecommendationFrequency.MONTHLY: 30,
            RecommendationFrequency.QUARTERLY: 90
        }
        
        days = frequency_map.get(user.recommendation_frequency, 7)
        threshold_date = datetime.utcnow() - timedelta(days=days)
        
        # Pour chaque terrain et parcelle de l'utilisateur
        for terrain in user.terrains:
            for parcelle in terrain.parcelles:
                # Vérifier la dernière recommandation pour cette parcelle
                latest_rec = db.query(Recommendation)\
                    .filter(Recommendation.parcelle_id == parcelle.id)\
                    .order_by(Recommendation.created_at.desc())\
                    .first()
                
                # Si pas de recommandation ou si la dernière est trop ancienne
                if not latest_rec or latest_rec.created_at < threshold_date:
                    logger.info(f"Déclenchement recommandation auto pour la parcelle {parcelle.id} (User: {user.email})")
                    try:
                        from app.services.recommendation_service import RecommendationService
                        await RecommendationService.run_unified_recommendation(
                            db=db,
                            user=user,
                            parcelle_id=str(parcelle.id)
                        )
                    except Exception as e:
                        logger.error(f"Échec recommandation auto pour parcelle {parcelle.id}: {str(e)}")

scheduler_service = SchedulerService()
