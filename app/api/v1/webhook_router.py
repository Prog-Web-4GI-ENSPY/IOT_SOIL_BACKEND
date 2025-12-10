"""
Router pour les webhooks ChirpStack et l'intégration ML
"""
from fastapi import APIRouter, Depends, status, Body, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.core.dependencies import get_current_user
from app.services.chirpstack_service import chirpstack_service
from app.services.ml_service import ml_service
from app.models.user import User


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks & Intégration"]
)


@router.post(
    "/chirpstack/uplink",
    status_code=status.HTTP_200_OK,
    summary="Webhook pour les données uplink de ChirpStack"
)
async def chirpstack_uplink_webhook(
    uplink_data: Dict[str, Any] = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Endpoint webhook pour recevoir les données uplink de ChirpStack.

    **Configuration dans ChirpStack:**
    1. Aller dans Applications > Votre Application > Integrations
    2. Ajouter "HTTP Integration"
    3. URL: `https://votre-domaine.com/api/v1/webhooks/chirpstack/uplink`
    4. Headers: Optionnel (pour sécurité)

    **Format des données attendues:**
    ```json
    {
        "devEUI": "0123456789abcdef",
        "data": {
            "temperature": 25.5,
            "humidity": 65.0,
            "soilMoisture": 45.0,
            ...
        },
        "rxInfo": [...],
        "txInfo": {...}
    }
    ```

    **Flux automatique:**
    1. Réception des données de ChirpStack
    2. Stockage dans la base de données
    3. Mise à jour du statut du capteur
    4. Envoi automatique au modèle ML (en arrière-plan)
    5. Génération automatique de recommandations
    """
    try:
        # Traiter les données uplink et créer la mesure
        measurement = await chirpstack_service.process_uplink_data(db, uplink_data)

        # Lancer le traitement ML en arrière-plan
        # On récupère l'user_id depuis le capteur/parcelle/terrain
        from app.models.capteur import Capteur
        from app.models.parcelle import Parcelle
        from app.models.terrain import Terrain

        capteur = db.query(Capteur).filter(
            Capteur.id == measurement.capteur_id
        ).first()

        if capteur and capteur.parcelle:
            parcelle = capteur.parcelle
            if parcelle.terrain:
                user_id = str(parcelle.terrain.user_id)

                # Traiter avec ML en arrière-plan
                background_tasks.add_task(
                    ml_service.process_sensor_data_with_ml,
                    db,
                    measurement,
                    user_id
                )

        return {
            "status": "success",
            "message": "Données reçues et traitées avec succès",
            "measurement_id": str(measurement.id),
            "ml_processing": "scheduled"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post(
    "/chirpstack/join",
    status_code=status.HTTP_200_OK,
    summary="Webhook pour les événements join de ChirpStack"
)
async def chirpstack_join_webhook(
    join_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint webhook pour les événements de join (connexion d'un device).

    Met à jour le statut du capteur lorsqu'il se connecte au réseau.
    """
    try:
        dev_eui = join_data.get("devEUI")

        from app.services.capteur_service import capteur_service
        from app.models.capteur import StatutCapteur
        from datetime import datetime

        capteur = capteur_service.get_capteur_by_dev_eui(db, dev_eui)

        if capteur:
            capteur_service.update_capteur_status(
                db=db,
                capteur_id=str(capteur.id),
                statut=StatutCapteur.ONLINE,
                last_seen=datetime.utcnow()
            )

        return {
            "status": "success",
            "message": "Événement join traité"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post(
    "/chirpstack/status",
    status_code=status.HTTP_200_OK,
    summary="Webhook pour les événements de statut ChirpStack"
)
async def chirpstack_status_webhook(
    status_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint webhook pour les événements de statut (batterie faible, erreurs, etc.).
    """
    try:
        dev_eui = status_data.get("devEUI")
        margin = status_data.get("margin", 0)  # Marge de démodulation
        battery = status_data.get("battery", None)

        from app.services.capteur_service import capteur_service
        from app.models.capteur import StatutCapteur

        capteur = capteur_service.get_capteur_by_dev_eui(db, dev_eui)

        if capteur:
            # Déterminer le statut basé sur les informations
            statut = StatutCapteur.ONLINE

            if battery and battery < 20:
                statut = StatutCapteur.BATTERIE_FAIBLE

            capteur_service.update_capteur_status(
                db=db,
                capteur_id=str(capteur.id),
                statut=statut,
                battery_level=battery
            )

        return {
            "status": "success",
            "message": "Statut mis à jour"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post(
    "/ml/trigger/{capteur_id}",
    summary="Déclencher manuellement l'analyse ML"
)
async def trigger_ml_analysis(
    capteur_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Déclencher manuellement une analyse ML pour un capteur spécifique.

    Utile pour tester ou forcer une nouvelle analyse sans attendre de nouvelles données.

    **Retourne:**
    - Recommandation générée par le ML
    - Prédiction si applicable
    """
    try:
        # Créer la recommandation
        recommendation = await ml_service.create_recommendation_from_ml(
            db, capteur_id, str(current_user.id)
        )

        # Créer la prédiction
        from app.models.capteur import Capteur
        capteur = db.query(Capteur).filter(Capteur.id == capteur_id).first()

        prediction = None
        if capteur:
            prediction = await ml_service.create_prediction_from_ml(
                db, capteur_id, str(capteur.parcelle_id)
            )

        return {
            "status": "success",
            "recommendation": {
                "id": str(recommendation.id),
                "titre": recommendation.titre,
                "priorite": recommendation.priorite.value
            },
            "prediction": {
                "id": str(prediction.id),
                "type": prediction.type_prediction,
                "valeur": prediction.valeur_predite
            } if prediction else None
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post(
    "/ml/batch-analysis",
    summary="Analyse ML en batch pour tous les capteurs"
)
async def batch_ml_analysis(
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Lancer une analyse ML pour tous les capteurs de l'utilisateur.

    Traitement en arrière-plan pour éviter les timeouts.
    """
    from app.models.capteur import Capteur, StatutCapteur
    from app.models.parcelle import Parcelle
    from app.models.terrain import Terrain

    # Récupérer tous les capteurs actifs de l'utilisateur
    capteurs = db.query(Capteur).join(Parcelle).join(Terrain).filter(
        Terrain.user_id == current_user.id,
        Capteur.statut == StatutCapteur.ONLINE
    ).all()

    # Lancer l'analyse pour chaque capteur en arrière-plan
    for capteur in capteurs:
        background_tasks.add_task(
            ml_service.create_recommendation_from_ml,
            db,
            str(capteur.id),
            str(current_user.id)
        )

    return {
        "status": "success",
        "message": f"Analyse ML lancée pour {len(capteurs)} capteurs",
        "capteurs_count": len(capteurs)
    }


@router.get(
    "/chirpstack/sync-devices",
    summary="Synchroniser les devices depuis ChirpStack"
)
async def sync_chirpstack_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Synchroniser tous les devices de l'application ChirpStack avec la base de données.

    Met à jour les informations des capteurs existants.
    """
    stats = await chirpstack_service.sync_devices(db)

    return {
        "status": "success",
        "statistics": stats
    }


@router.get(
    "/status",
    summary="Statut des services d'intégration"
)
async def integration_status():
    """
    Vérifier le statut des services d'intégration (ChirpStack et ML).
    """
    from app.core.config import settings

    return {
        "chirpstack": {
            "configured": bool(settings.CHIRPSTACK_API_URL and settings.CHIRPSTACK_API_TOKEN),
            "api_url": str(settings.CHIRPSTACK_API_URL) if settings.CHIRPSTACK_API_URL else None
        },
        "ml_service": {
            "configured": True,
            "api_url": ml_service.ml_api_url
        }
    }
