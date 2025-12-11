"""
Router pour l'intégration avec le Système Expert
Gère l'envoi des données et la réception des recommandations
"""
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.sensor_data import SensorMeasurements
from app.models.capteur import Capteur
from app.models.parcelle import Parcelle
from app.models.recommendation import Recommendation


router = APIRouter(
    prefix="/expert-system",
    tags=["Système Expert"]
)


# ============================================================================
# SCHEMAS POUR L'ÉCHANGE AVEC LE SYSTÈME EXPERT
# ============================================================================

class SensorDataForExpert(Dict[str, Any]):
    """
    Format des données à envoyer au système expert

    Structure attendue:
    {
        "capteur_id": "uuid",
        "parcelle_id": "uuid",
        "terrain_info": {
            "superficie": 2.5,
            "type_sol": "Argileux"
        },
        "measurements": [
            {
                "timestamp": "2025-12-10T10:30:00",
                "temperature": 25.5,
                "humidity": 65.0,
                "soil_moisture": 45.0,
                "ph": 6.5,
                "nitrogen": 50,
                "phosphorus": 30,
                "potassium": 40
            }
        ],
        "statistics": {
            "temperature_avg": 24.8,
            "humidity_avg": 63.2,
            ...
        }
    }
    """
    pass


class ExpertRecommendation(Dict[str, Any]):
    """
    Format des recommandations reçues du système expert

    Structure attendue:
    {
        "titre": "Irrigation recommandée",
        "contenu": "L'humidité du sol est faible...",
        "priorite": "Urgent",
        "culture_recommandee": "Maïs",
        "actions": [
            "Irriguer 20mm",
            "Vérifier le drainage"
        ],
        "predictions": {
            "rendement_estime": 4500,
            "risques": ["Sécheresse"],
            "confidence": 0.85
        }
    }
    """
    pass


# ============================================================================
# ENDPOINTS - ENVOI DES DONNÉES AU SYSTÈME EXPERT
# ============================================================================

@router.post(
    "/send-data/{capteur_id}",
    summary="Envoyer les données d'un capteur au système expert"
)
async def send_sensor_data_to_expert(
    capteur_id: str,
    n_measurements: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Prépare et retourne les données d'un capteur au format attendu par le système expert.

    **Ce endpoint prépare les données pour l'envoi au système expert.**
    Le système expert externe appellera ensuite `/receive-recommendation` pour renvoyer les recommandations.

    Args:
        capteur_id: ID du capteur
        n_measurements: Nombre de mesures récentes à inclure (défaut: 100)

    Returns:
        Données formatées prêtes à être envoyées au système expert
    """
    # Récupérer le capteur
    capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()

    if not capteur:
        return {
            "error": "Capteur non trouvé",
            "capteur_id": capteur_id
        }

    # Récupérer la parcelle
    parcelle = db.query(Parcelle).filter(Parcelle.id == capteur.parcelle_id).first()

    # Récupérer les dernières mesures
    measurements = db.query(SensorMeasurements).filter(
        SensorMeasurements.capteur_id == capteur_id
    ).order_by(
        SensorMeasurements.timestamp.desc()
    ).limit(n_measurements).all()

    if not measurements:
        return {
            "error": "Aucune mesure trouvée pour ce capteur",
            "capteur_id": capteur_id
        }

    # Calculer les statistiques
    stats = _calculate_statistics(measurements)

    # Préparer les données au format expert
    data_for_expert = {
        "capteur_id": str(capteur.id),
        "capteur_type": capteur.type_capteur,
        "parcelle_id": str(parcelle.id) if parcelle else None,
        "parcelle_info": {
            "superficie": float(parcelle.superficie) if parcelle else None,
            "type_sol": parcelle.type_sol if parcelle else None,
            "culture_actuelle": parcelle.culture_actuelle if parcelle else None
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
        "statistics": stats,
        "generated_at": datetime.utcnow().isoformat()
    }

    return {
        "status": "success",
        "message": "Données préparées pour le système expert",
        "data": data_for_expert
    }


@router.post(
    "/send-parcelle-data/{parcelle_id}",
    summary="Envoyer les données de tous les capteurs d'une parcelle"
)
async def send_parcelle_data_to_expert(
    parcelle_id: str,
    n_measurements: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Prépare les données de tous les capteurs d'une parcelle pour le système expert.

    Args:
        parcelle_id: ID de la parcelle
        n_measurements: Nombre de mesures par capteur

    Returns:
        Données de tous les capteurs de la parcelle
    """
    # Récupérer la parcelle
    parcelle = db.query(Parcelle).filter(Parcelle.id == parcelle_id).first()

    if not parcelle:
        return {
            "error": "Parcelle non trouvée",
            "parcelle_id": parcelle_id
        }

    # Récupérer tous les capteurs de la parcelle
    capteurs = db.query(Capteur).filter(Capteur.parcelle_id == parcelle_id).all()

    if not capteurs:
        return {
            "error": "Aucun capteur trouvé pour cette parcelle",
            "parcelle_id": parcelle_id
        }

    # Préparer les données pour chaque capteur
    capteurs_data = []
    for capteur in capteurs:
        measurements = db.query(SensorMeasurements).filter(
            SensorMeasurements.capteur_id == str(capteur.id)
        ).order_by(
            SensorMeasurements.timestamp.desc()
        ).limit(n_measurements).all()

        if measurements:
            capteurs_data.append({
                "capteur_id": str(capteur.id),
                "capteur_type": capteur.type_capteur,
                "measurements": [
                    {
                        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                        "temperature": float(m.temperature) if m.temperature else None,
                        "humidity": float(m.humidity) if m.humidity else None,
                        "soil_moisture": float(m.soil_moisture) if m.soil_moisture else None,
                        "ph": float(m.ph) if m.ph else None,
                        "nitrogen": float(m.nitrogen) if m.nitrogen else None,
                        "phosphorus": float(m.phosphorus) if m.phosphorus else None,
                        "potassium": float(m.potassium) if m.potassium else None
                    }
                    for m in measurements
                ],
                "statistics": _calculate_statistics(measurements)
            })

    data_for_expert = {
        "parcelle_id": str(parcelle.id),
        "parcelle_info": {
            "nom": parcelle.nom,
            "superficie": float(parcelle.superficie),
            "type_sol": parcelle.type_sol,
            "culture_actuelle": parcelle.culture_actuelle
        },
        "capteurs": capteurs_data,
        "generated_at": datetime.utcnow().isoformat()
    }

    return {
        "status": "success",
        "message": f"Données de {len(capteurs_data)} capteurs préparées",
        "data": data_for_expert
    }


# ============================================================================
# ENDPOINTS - RÉCEPTION DES RECOMMANDATIONS DU SYSTÈME EXPERT
# ============================================================================

@router.post(
    "/receive-recommendation",
    status_code=status.HTTP_201_CREATED,
    summary="Recevoir une recommandation du système expert"
)
async def receive_expert_recommendation(
    recommendation_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Endpoint appelé par le système expert pour envoyer ses recommandations.

    **Format attendu:**
    ```json
    {
        "parcelle_id": "uuid",
        "titre": "Irrigation recommandée",
        "contenu": "Description détaillée...",
        "priorite": "Urgent",
        "culture_recommandee": "Maïs",
        "actions": ["Action 1", "Action 2"],
        "predictions": {
            "rendement_estime": 4500,
            "risques": ["Sécheresse"],
            "confidence": 0.85
        }
    }
    ```

    Returns:
        Confirmation de la sauvegarde
    """
    try:
        # Extraire les données
        parcelle_id = recommendation_data.get("parcelle_id")
        titre = recommendation_data.get("titre", "Recommandation du système expert")
        contenu = recommendation_data.get("contenu", "")
        priorite = recommendation_data.get("priorite", "Normal")

        # Vérifier que la parcelle existe
        parcelle = db.query(Parcelle).filter(Parcelle.id == parcelle_id).first()
        if not parcelle:
            return {
                "status": "error",
                "message": "Parcelle non trouvée",
                "parcelle_id": parcelle_id
            }

        # Récupérer user_id depuis la parcelle
        user_id = str(parcelle.terrain.user_id) if parcelle.terrain else None

        if not user_id:
            return {
                "status": "error",
                "message": "Impossible de déterminer l'utilisateur"
            }

        # Créer la recommandation
        recommendation = Recommendation(
            titre=titre,
            contenu=contenu,
            parcelle_id=parcelle_id,
            user_id=user_id,
            priorite=priorite,
            expert_metadata={
                "source": "expert_system",
                "culture_recommandee": recommendation_data.get("culture_recommandee"),
                "actions": recommendation_data.get("actions", []),
                "predictions": recommendation_data.get("predictions", {}),
                "received_at": datetime.utcnow().isoformat()
            }
        )

        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)

        return {
            "status": "success",
            "message": "Recommandation enregistrée avec succès",
            "recommendation_id": str(recommendation.id),
            "parcelle_id": parcelle_id
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Erreur lors de l'enregistrement: {str(e)}"
        }


@router.post(
    "/receive-recommendations-batch",
    status_code=status.HTTP_201_CREATED,
    summary="Recevoir plusieurs recommandations du système expert"
)
async def receive_expert_recommendations_batch(
    recommendations: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Endpoint pour recevoir plusieurs recommandations en une seule fois.

    **Format attendu:**
    ```json
    [
        {
            "parcelle_id": "uuid1",
            "titre": "...",
            "contenu": "...",
            ...
        },
        {
            "parcelle_id": "uuid2",
            "titre": "...",
            ...
        }
    ]
    ```

    Returns:
        Résumé des recommandations enregistrées
    """
    results = {
        "success": 0,
        "errors": 0,
        "details": []
    }

    for rec_data in recommendations:
        try:
            parcelle_id = rec_data.get("parcelle_id")
            parcelle = db.query(Parcelle).filter(Parcelle.id == parcelle_id).first()

            if not parcelle:
                results["errors"] += 1
                results["details"].append({
                    "parcelle_id": parcelle_id,
                    "status": "error",
                    "message": "Parcelle non trouvée"
                })
                continue

            user_id = str(parcelle.terrain.user_id) if parcelle.terrain else None

            if not user_id:
                results["errors"] += 1
                results["details"].append({
                    "parcelle_id": parcelle_id,
                    "status": "error",
                    "message": "Utilisateur non trouvé"
                })
                continue

            recommendation = Recommendation(
                titre=rec_data.get("titre", "Recommandation"),
                contenu=rec_data.get("contenu", ""),
                parcelle_id=parcelle_id,
                user_id=user_id,
                priorite=rec_data.get("priorite", "Normal"),
                expert_metadata={
                    "source": "expert_system",
                    "culture_recommandee": rec_data.get("culture_recommandee"),
                    "actions": rec_data.get("actions", []),
                    "predictions": rec_data.get("predictions", {}),
                    "received_at": datetime.utcnow().isoformat()
                }
            )

            db.add(recommendation)
            results["success"] += 1
            results["details"].append({
                "parcelle_id": parcelle_id,
                "status": "success"
            })

        except Exception as e:
            results["errors"] += 1
            results["details"].append({
                "parcelle_id": rec_data.get("parcelle_id"),
                "status": "error",
                "message": str(e)
            })

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Erreur lors de la sauvegarde: {str(e)}"
        }

    return {
        "status": "success",
        "message": f"{results['success']} recommandations enregistrées, {results['errors']} erreurs",
        "results": results
    }


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def _calculate_statistics(measurements: List[SensorMeasurements]) -> Dict[str, Any]:
    """Calculer les statistiques sur les mesures"""
    if not measurements:
        return {}

    stats = {}
    fields = ["temperature", "humidity", "soil_moisture", "ph", "nitrogen", "phosphorus", "potassium"]

    for field in fields:
        values = [
            float(getattr(m, field)) for m in measurements
            if getattr(m, field) is not None
        ]

        if values:
            stats[f"{field}_avg"] = sum(values) / len(values)
            stats[f"{field}_min"] = min(values)
            stats[f"{field}_max"] = max(values)
            stats[f"{field}_count"] = len(values)

    return stats
