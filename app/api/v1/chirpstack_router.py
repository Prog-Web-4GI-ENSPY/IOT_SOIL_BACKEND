"""
Router pour les webhooks ChirpStack
"""
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.chirpstack_service import chirpstack_service


router = APIRouter(
    prefix="/chirpstack",
    tags=["ChirpStack"]
)


@router.post(
    "/uplink",
    status_code=status.HTTP_200_OK,
    summary="Webhook pour les données uplink de ChirpStack"
)
async def chirpstack_uplink_webhook(
    uplink_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint webhook pour recevoir les données uplink de ChirpStack.

    **Configuration dans ChirpStack:**
    1. Aller dans Applications > Votre Application > Integrations
    2. Ajouter "HTTP Integration"
    3. URL: `https://votre-domaine.com/api/v1/chirpstack/uplink`
    4. Method: POST

    **Format des données attendues:**
    ```json
    {
        "devEUI": "0123456789abcdef",
        "data": {
            "temperature": 25.5,
            "humidity": 65.0,
            "soilMoisture": 45.0,
            "ph": 6.5,
            "nitrogen": 50,
            "phosphorus": 30,
            "potassium": 40,
            "lightIntensity": 800,
            "batteryVoltage": 3.7
        },
        "rxInfo": [{
            "rssi": -80,
            "loRaSNR": 8.5
        }],
        "txInfo": {
            "frequency": 868100000
        }
    }
    ```

    **Ce qui se passe:**
    1. Réception des données du capteur
    2. Stockage dans la table `sensor_measurements`
    3. Mise à jour du statut du capteur
    """
    try:
        # Traiter les données uplink et créer la mesure
        measurement = await chirpstack_service.process_uplink_data(db, uplink_data)

        return {
            "status": "success",
            "message": "Données reçues et stockées",
            "measurement_id": str(measurement.id),
            "capteur_id": str(measurement.capteur_id)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post(
    "/join",
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

        from app.models.capteur import Capteur, StatutCapteur
        from datetime import datetime

        capteur = db.query(Capteur).filter(Capteur.dev_eui == dev_eui).first()

        if capteur:
            capteur.statut = StatutCapteur.ONLINE
            capteur.last_seen = datetime.utcnow()
            db.commit()

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
    "/status",
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
        battery = status_data.get("battery", None)

        from app.models.capteur import Capteur, StatutCapteur

        capteur = db.query(Capteur).filter(Capteur.dev_eui == dev_eui).first()

        if capteur:
            # Déterminer le statut basé sur les informations
            statut = StatutCapteur.ONLINE

            if battery and battery < 20:
                statut = StatutCapteur.BATTERIE_FAIBLE
                capteur.battery_level = battery

            capteur.statut = statut
            db.commit()

        return {
            "status": "success",
            "message": "Statut mis à jour"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get(
    "/sync-devices",
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


@router.post(
    "/send-downlink/{dev_eui}",
    summary="Envoyer une commande downlink à un device"
)
async def send_downlink_command(
    dev_eui: str,
    data: str = Body(..., description="Données en hexadécimal (ex: '01FF')"),
    f_port: int = Body(1, description="Port LoRaWAN"),
    confirmed: bool = Body(False, description="Demander un ACK"),
    current_user: User = Depends(get_current_user)
):
    """
    Envoyer une commande downlink à un device via ChirpStack.

    Args:
        dev_eui: DevEUI du capteur
        data: Données en hexadécimal (ex: "01FF")
        f_port: Port LoRaWAN (défaut: 1)
        confirmed: Si True, demande un ACK du device

    Example:
    ```json
    {
        "data": "01FF",
        "f_port": 1,
        "confirmed": false
    }
    ```
    """
    try:
        # Convertir hex string en bytes
        data_bytes = bytes.fromhex(data)

        result = await chirpstack_service.send_downlink(
            dev_eui=dev_eui,
            data=data_bytes,
            f_port=f_port,
            confirmed=confirmed
        )

        return {
            "status": "success",
            "message": "Commande envoyée",
            "result": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get(
    "/device-info/{dev_eui}",
    summary="Récupérer les informations d'un device"
)
async def get_device_info(
    dev_eui: str,
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les informations d'un device depuis ChirpStack.
    """
    try:
        info = await chirpstack_service.get_device_info(dev_eui)

        return {
            "status": "success",
            "data": info
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get(
    "/status",
    summary="Statut de la connexion ChirpStack"
)
async def chirpstack_connection_status():
    """
    Vérifier le statut de la connexion ChirpStack.
    """
    from app.core.config import settings

    return {
        "configured": bool(settings.CHIRPSTACK_API_URL and settings.CHIRPSTACK_API_TOKEN),
        "api_url": str(settings.CHIRPSTACK_API_URL) if settings.CHIRPSTACK_API_URL else None,
        "application_id": settings.CHIRPSTACK_APPLICATION_ID if settings.CHIRPSTACK_APPLICATION_ID else None
    }
