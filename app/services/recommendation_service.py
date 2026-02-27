from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationCreate, RecommendationUpdate
from datetime import datetime
import uuid
import logging
from app.services.ml_service import MLService
from app.services.expert_system_service import ExpertSystemService
from app.services.notification_service import NotificationService
from app.models.sensor_data import SensorMeasurements
from app.models.parcelle import Parcelle
from sqlalchemy import func

logger = logging.getLogger(__name__)


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

    @staticmethod
    async def run_unified_recommendation(
        db: Session,
        user: any,
        background_tasks: any,
        parcelle_id: Optional[str] = None,
        soil_data: Optional[any] = None,
        region: Optional[str] = None,
        query: Optional[str] = None
    ) -> dict:
        """
        Orchestre une recommandation complète (ML + Système Expert) avec notifications.
        Exécute le ML en temps réel, et lance le Système Expert + Notifications en arrière-plan.
        """


        # 1. Obtenir les données du sol
        final_soil_data_batch = []
        parcelle = None
        
        if parcelle_id:
            parcelle = db.query(Parcelle).filter(Parcelle.id == parcelle_id).first()
            if not parcelle:
                raise HTTPException(status_code=404, detail="Parcelle non trouvée")
            
            # Récupérer les mesures les plus récentes si soil_data n'est pas fourni
            if not soil_data:
                latest_timestamp = db.query(func.max(SensorMeasurements.timestamp))\
                    .filter(SensorMeasurements.parcelle_id == parcelle_id).scalar()
                
                if latest_timestamp:
                    daily_measurements = db.query(SensorMeasurements)\
                        .filter(SensorMeasurements.parcelle_id == parcelle_id,
                                func.date(SensorMeasurements.timestamp) == latest_timestamp.date())\
                        .order_by(SensorMeasurements.timestamp.desc()).all()
                    
                    from app.schemas.ai_integration import SoilData
                    final_soil_data_batch = [
                        SoilData(
                            N=max(int(m.azote or 1), 1),  # ML service requires > 0
                            P=max(int(m.phosphore or 1), 1),  # ML service requires > 0
                            K=max(int(m.potassium or 1), 1),  # ML service requires > 0
                            temperature=max(m.temperature or 20.0, 0.1),
                            humidity=max(m.humidity or 50.0, 0.1),
                            ph=max(m.ph or 6.5, 0.1),
                            rainfall=1500.0  # Default rainfall in mm/year for regions like Centre
                        ) for m in daily_measurements
                    ]
        
        if not final_soil_data_batch and soil_data:
            final_soil_data_batch = [soil_data] if not isinstance(soil_data, list) else soil_data

        if not final_soil_data_batch:
            raise HTTPException(status_code=400, detail="Données du sol insuffisantes pour la prédiction.")

        # Validation: s'assurer que toutes les valeurs respectent les contraintes du ML service
        for idx, sd in enumerate(final_soil_data_batch):
            if sd.N <= 0:
                final_soil_data_batch[idx].N = 1
            if sd.P <= 0:
                final_soil_data_batch[idx].P = 1
            if sd.K <= 0:
                final_soil_data_batch[idx].K = 1
            if sd.temperature <= 0:
                final_soil_data_batch[idx].temperature = 20.0
            if sd.humidity <= 0:
                final_soil_data_batch[idx].humidity = 50.0
            if sd.ph <= 0:
                final_soil_data_batch[idx].ph = 6.5

        # 2. ML Prediction
        ml_result = await MLService.predict_crop(final_soil_data_batch)
        recommended_crop = ml_result.top3_global[0].culture if ml_result.top3_global else "Inconnu"
        confidence = ml_result.top3_global[0].confiance_agregee if ml_result.top3_global else 0.0

        # Lancement de la tâche de fond pour l'enrichissement par le système expert et les notifications
        current_region = region or (parcelle.terrain.localite.region if parcelle and parcelle.terrain and parcelle.terrain.localite else "Centre")
        background_tasks.add_task(
            RecommendationService.run_expert_system_and_notify,
            user=user,
            parcelle_id=parcelle_id,
            recommended_crop=recommended_crop,
            ml_result=ml_result,
            current_region=current_region,
            query=query
        )

        from app.schemas.ai_integration import UnifiedRecommendationResponse
        return UnifiedRecommendationResponse(
            recommended_crop=recommended_crop,
            confidence_score=confidence,
            justification="L'analyse détaillée par notre système expert est en cours de génération et vous sera envoyée d'ici quelques instants.",
            detailed_justifications={},
            ml_details=ml_result,
            generated_at=datetime.utcnow().isoformat()
        )

    @staticmethod
    async def run_expert_system_and_notify(
        user: any,
        parcelle_id: Optional[str],
        recommended_crop: str,
        ml_result: any,
        current_region: str,
        query: Optional[str]
    ):
        """
        Exécution asynchrone du système expert, sauvegarde en base de données et envoi des notifications.
        """
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            # 3. Système Expert (4 questions)
            user_query = None if query in ["string", ""] else query
    
            queries = {
                "plantation": user_query or f"Quelle est la période optimale de plantation pour le {recommended_crop} dans la région {current_region} ?",
                "irrigation": f"Quels sont les besoins en irrigation spécifiques pour le {recommended_crop} ?",
                "engrais": f"Quels engrais et amendements du sol recommandez-vous pour le {recommended_crop} ?",
                "prevention": f"Comment prévenir les maladies et ravageurs communs du {recommended_crop} ?"
            }
    
            results_justification = {}
            full_justification = ""
            
            for key, q in queries.items():
                expert_res = await ExpertSystemService.query_expert_system(query=q, region=current_region)
                resp_text = expert_res.final_response if expert_res else "Pas de réponse disponible."
                results_justification[key] = resp_text
                full_justification += f"\n\n### {key.capitalize()}\n{resp_text}"
    
            # 4. Sauvegarde DB
            new_rec = Recommendation(
                id=str(uuid.uuid4()),
                titre=f"Analyse Complète pour {recommended_crop}",
                contenu=full_justification.strip(),
                priorite="Normal",
                parcelle_id=parcelle_id if parcelle_id else None,
                user_id=str(user.id),
                expert_metadata={
                    "source": "Service_Orchestrator",
                    "ml_confidence": ml_result.top3_global[0].confiance_agregee if ml_result.top3_global else 0.0,
                    "recommended_crop": recommended_crop,
                    "detailed_responses": results_justification,
                    "ml_details": ml_result.dict()
                }
            )
            db.add(new_rec)
            db.commit()
            db.refresh(new_rec)
    
            # 5. Notifications
            notif_service = NotificationService()
            user_pref_modes = getattr(user, 'notification_modes', ['email'])
            
            # ---- Préparation des messages ----
            # Email : 1 message résumé + 4 messages détaillés (un par catégorie)
            confidence = ml_result.top3_global[0].confiance_agregee if ml_result.top3_global else 0.0
            email_messages = [(
                f"AgroPredict: Recommandation globale",
                f"Culture recommandée: {recommended_crop}\nConfiance: {confidence:.2f}%"
            )]
            for category, response_text in results_justification.items():
                email_messages.append((
                    f"AgroPredict ({category.capitalize()}): {recommended_crop}",
                    f"Catégorie: {category.capitalize()}\n\n{response_text}"
                ))

            # SMS/WhatsApp/Telegram : 1 seul message résumé (économie de crédits)
            short_summary = (
                f"[AgroPredict] Culture: {recommended_crop} | Confiance: {confidence:.2f}%\n"
                f"Détails complets envoyés par email."
            )
            
            # ---- Envoi par canal ----
            for mode_raw in user_pref_modes:
                mode = str(mode_raw).lower()
                if "." in mode:
                    mode = mode.split(".")[-1]
                
                logger.info(f"Processing notifications for mode: {mode}")
                try:
                    if mode == 'email':
                        for title, body in email_messages:
                            await notif_service.send_email(user.email, title, body)
                            logger.info(f"Email sent for '{title}'")
                    elif mode == 'sms' and user.telephone:
                        # 1 seul SMS résumé pour économiser les crédits
                        res = await notif_service.send_sms(user.telephone, short_summary)
                        logger.info(f"SMS send result: {res}")
                    elif mode == 'whatsapp' and user.telephone:
                        await notif_service.send_whatsapp(user.telephone, short_summary)
                    elif mode == 'telegram':
                        await notif_service.send_telegram(short_summary)
                except Exception as e:
                    logger.error(f"Erreur notification ({mode}) via background task: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur globale dans le traitement asynchrone de la recommandation: {str(e)}")
        finally:
            db.close()