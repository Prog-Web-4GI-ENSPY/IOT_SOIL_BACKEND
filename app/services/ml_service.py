"""
Service pour l'intégration avec le modèle de Machine Learning
Gère l'envoi des données et la réception des recommandations
"""
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.sensor_data import SensorMeasurements
from app.models.recommendation import Recommendation
from app.models.prediction import Prediction
from app.models.parcelle import Parcelle
from app.models.capteur import Capteur


class MLService:
    """Service pour interagir avec le modèle de Machine Learning"""

    def __init__(self):
        # URL du service ML - à configurer dans .env
        self.ml_api_url = "http://localhost:5000"  # À adapter selon votre config
        self.timeout = 60.0  # Timeout pour les requêtes ML

    async def prepare_sensor_data_for_ml(
        self,
        db: Session,
        capteur_id: str,
        last_n_measurements: int = 100
    ) -> Dict[str, Any]:
        """
        Préparer les données du capteur pour l'envoi au modèle ML

        Args:
            db: Session de base de données
            capteur_id: ID du capteur
            last_n_measurements: Nombre de mesures récentes à inclure

        Returns:
            Données formatées pour le ML
        """
        # Récupérer les dernières mesures
        measurements = db.query(SensorMeasurements).filter(
            SensorMeasurements.capteur_id == capteur_id
        ).order_by(
            SensorMeasurements.timestamp.desc()
        ).limit(last_n_measurements).all()

        if not measurements:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune mesure trouvée pour ce capteur"
            )

        # Récupérer les informations du capteur et de la parcelle
        capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()
        parcelle = db.query(Parcelle).filter(Parcelle.id == capteur.parcelle_id).first()

        # Préparer le payload pour le ML
        data = {
            "capteur_info": {
                "id": str(capteur.id),
                "type": capteur.type_capteur,
                "dev_eui": capteur.dev_eui
            },
            "parcelle_info": {
                "id": str(parcelle.id),
                "superficie": float(parcelle.superficie),
                "type_sol": parcelle.type_sol,
                "culture_actuelle": parcelle.culture_actuelle
            },
            "measurements": [
                {
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "temperature": float(m.temperature) if m.temperature else None,
                    "humidity": float(m.humidity) if m.humidity else None,
                    "soil_moisture": float(m.soil_moisture) if m.soil_moisture else None,
                    "ph": float(m.ph) if m.ph else None,
                    "nitrogen": float(m.nitrogen) if m.nitrogen else None,
                    "phosphorus": float(m.phosphorus) if m.phosphorus else None,
                    "potassium": float(m.potassium) if m.potassium else None,
                    "light_intensity": float(m.light_intensity) if m.light_intensity else None
                }
                for m in measurements
            ],
            "statistics": self._calculate_statistics(measurements)
        }

        return data

    def _calculate_statistics(
        self,
        measurements: List[SensorMeasurements]
    ) -> Dict[str, Any]:
        """Calculer des statistiques sur les mesures"""
        if not measurements:
            return {}

        stats = {}
        fields = [
            "temperature", "humidity", "soil_moisture",
            "ph", "nitrogen", "phosphorus", "potassium"
        ]

        for field in fields:
            values = [
                getattr(m, field) for m in measurements
                if getattr(m, field) is not None
            ]

            if values:
                stats[field] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }

        return stats

    async def get_ml_recommendation(
        self,
        db: Session,
        capteur_id: str
    ) -> Dict[str, Any]:
        """
        Envoyer les données au modèle ML et récupérer la recommandation

        Args:
            db: Session de base de données
            capteur_id: ID du capteur

        Returns:
            Recommandation du modèle ML
        """
        try:
            # Préparer les données
            ml_data = await self.prepare_sensor_data_for_ml(db, capteur_id)

            # Envoyer au modèle ML
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ml_api_url}/api/predict",
                    json=ml_data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                ml_response = response.json()

            return ml_response

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur lors de la communication avec le service ML: {str(e)}"
            )

    async def create_recommendation_from_ml(
        self,
        db: Session,
        capteur_id: str,
        user_id: str
    ) -> Recommendation:
        """
        Créer automatiquement une recommandation basée sur l'analyse ML

        Args:
            db: Session de base de données
            capteur_id: ID du capteur
            user_id: ID de l'utilisateur

        Returns:
            Recommandation créée
        """
        try:
            # Récupérer la recommandation du ML
            ml_response = await self.get_ml_recommendation(db, capteur_id)

            # Récupérer le capteur et la parcelle
            capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()

            if not capteur:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Capteur non trouvé"
                )

            # Extraire les informations de la réponse ML
            titre = ml_response.get("titre", "Recommandation automatique")
            description = ml_response.get("description", "")
            priorite = ml_response.get("priorite", "Normal")

            # Créer la recommandation
            recommendation = Recommendation(
                titre=titre,
                contenu=description,
                parcelle_id=str(capteur.parcelle_id),
                user_id=user_id,
                priorite=priorite,
                source="ML_AUTO",
                metadata={
                    "capteur_id": str(capteur_id),
                    "ml_confidence": ml_response.get("confidence"),
                    "ml_model_version": ml_response.get("model_version"),
                    "generated_at": datetime.utcnow().isoformat()
                }
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

    async def create_prediction_from_ml(
        self,
        db: Session,
        capteur_id: str,
        parcelle_id: str
    ) -> Prediction:
        """
        Créer une prédiction basée sur l'analyse ML

        Args:
            db: Session de base de données
            capteur_id: ID du capteur
            parcelle_id: ID de la parcelle

        Returns:
            Prédiction créée
        """
        try:
            # Récupérer la réponse ML
            ml_response = await self.get_ml_recommendation(db, capteur_id)

            # Extraire les prédictions
            prediction_data = ml_response.get("prediction", {})

            prediction = Prediction(
                parcelle_id=parcelle_id,
                type_prediction=prediction_data.get("type", "yield"),
                valeur_predite=prediction_data.get("valeur_predite"),
                confiance=prediction_data.get("confiance", 0.0),
                date_prediction=datetime.utcnow(),
                modele_utilise=ml_response.get("model_version", "v1.0"),
                parametres_entree={
                    "capteur_id": str(capteur_id),
                    "n_measurements": len(ml_response.get("measurements_used", []))
                },
                metadata=prediction_data.get("metadata", {})
            )

            db.add(prediction)
            db.commit()
            db.refresh(prediction)

            return prediction

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création de la prédiction: {str(e)}"
            )

    async def process_sensor_data_with_ml(
        self,
        db: Session,
        measurement: SensorMeasurements,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Traiter automatiquement les nouvelles données de capteur avec le ML

        Cette fonction est appelée automatiquement après réception de nouvelles données

        Args:
            db: Session de base de données
            measurement: Mesure de capteur
            user_id: ID de l'utilisateur

        Returns:
            Résultats du traitement (recommandation et prédiction créées)
        """
        result = {
            "recommendation": None,
            "prediction": None,
            "processed": False
        }

        try:
            # Récupérer le capteur
            capteur = db.query(Capteur).filter(
                Capteur.id == measurement.capteur_id
            ).first()

            if not capteur:
                return result

            # Vérifier si on a assez de données pour faire une analyse
            measurement_count = db.query(SensorMeasurements).filter(
                SensorMeasurements.capteur_id == str(capteur.id)
            ).count()

            if measurement_count < 10:
                # Pas assez de données pour l'analyse ML
                return result

            # Créer une recommandation basée sur le ML
            recommendation = await self.create_recommendation_from_ml(
                db, str(capteur.id), user_id
            )
            result["recommendation"] = recommendation

            # Créer une prédiction si pertinent
            prediction = await self.create_prediction_from_ml(
                db, str(capteur.id), str(capteur.parcelle_id)
            )
            result["prediction"] = prediction

            result["processed"] = True

            return result

        except Exception as e:
            print(f"Erreur lors du traitement ML: {e}")
            return result


ml_service = MLService()
