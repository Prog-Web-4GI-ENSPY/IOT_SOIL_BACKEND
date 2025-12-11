"""
Service simplifié pour l'intégration avec ChirpStack
Gère uniquement la communication avec le serveur ChirpStack
"""
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.capteur import Capteur, StatutCapteur
from app.models.sensor_data import SensorMeasurements


class ChirpStackService:
    """Service pour interagir avec le serveur ChirpStack"""

    def __init__(self):
        self.api_url = str(settings.CHIRPSTACK_API_URL)
        self.api_token = settings.CHIRPSTACK_API_TOKEN
        self.application_id = settings.CHIRPSTACK_APPLICATION_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    # ========================================================================
    # RÉCEPTION DES DONNÉES DE CHIRPSTACK (UPLINK)
    # ========================================================================

    async def process_uplink_data(
        self,
        db: Session,
        uplink_data: Dict[str, Any]
    ) -> SensorMeasurements:
        """
        Traiter les données uplink reçues de ChirpStack via webhook

        Format attendu de uplink_data:
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

        Args:
            db: Session de base de données
            uplink_data: Données uplink de ChirpStack

        Returns:
            Mesure créée dans la base de données
        """
        try:
            # Extraire les informations du payload
            dev_eui = uplink_data.get("devEUI")
            data = uplink_data.get("data", {})

            # Trouver le capteur correspondant
            capteur = db.query(Capteur).filter(Capteur.dev_eui == dev_eui).first()

            if not capteur:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Capteur avec DevEUI {dev_eui} non trouvé"
                )

            # Extraire les métadonnées LoRaWAN
            rx_info = uplink_data.get("rxInfo", [{}])[0]
            tx_info = uplink_data.get("txInfo", {})

            # Créer la mesure
            measurement = SensorMeasurements(
                capteur_id=str(capteur.id),
                temperature=data.get("temperature"),
                humidity=data.get("humidity"),
                soil_moisture=data.get("soilMoisture") or data.get("soil_moisture"),
                ph=data.get("ph"),
                nitrogen=data.get("nitrogen"),
                phosphorus=data.get("phosphorus"),
                potassium=data.get("potassium"),
                light_intensity=data.get("lightIntensity") or data.get("light_intensity"),
                battery_voltage=data.get("batteryVoltage") or data.get("battery_voltage"),
                raw_data=data,
                rssi=rx_info.get("rssi"),
                snr=rx_info.get("loRaSNR"),
                frequency=tx_info.get("frequency")
            )

            db.add(measurement)

            # Mettre à jour le statut du capteur
            self._update_capteur_status(
                db=db,
                capteur=capteur,
                battery_voltage=data.get("batteryVoltage") or data.get("battery_voltage"),
                rssi=rx_info.get("rssi"),
                snr=rx_info.get("loRaSNR")
            )

            db.commit()
            db.refresh(measurement)

            return measurement

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors du traitement des données: {str(e)}"
            )

    def _update_capteur_status(
        self,
        db: Session,
        capteur: Capteur,
        battery_voltage: Optional[float] = None,
        rssi: Optional[int] = None,
        snr: Optional[float] = None
    ):
        """Mettre à jour le statut du capteur"""
        capteur.statut = StatutCapteur.ONLINE
        capteur.last_seen = datetime.utcnow()

        if battery_voltage is not None:
            battery_level = self._calculate_battery_level(battery_voltage)
            capteur.battery_level = battery_level

            # Mettre le statut à BATTERIE_FAIBLE si < 20%
            if battery_level < 20:
                capteur.statut = StatutCapteur.BATTERIE_FAIBLE

        if rssi is not None and snr is not None:
            capteur.signal_quality = self._calculate_signal_quality(rssi, snr)

        capteur.updated_at = datetime.utcnow()

    # ========================================================================
    # ENVOI DE COMMANDES VERS CHIRPSTACK (DOWNLINK)
    # ========================================================================

    async def send_downlink(
        self,
        dev_eui: str,
        data: bytes,
        f_port: int = 1,
        confirmed: bool = False
    ) -> Dict[str, Any]:
        """
        Envoyer une commande downlink à un device via ChirpStack

        Args:
            dev_eui: DevEUI du capteur
            data: Données à envoyer (bytes)
            f_port: Port LoRaWAN (défaut: 1)
            confirmed: Si True, demande un ACK du device

        Returns:
            Réponse de ChirpStack
        """
        try:
            payload = {
                "deviceQueueItem": {
                    "devEUI": dev_eui,
                    "confirmed": confirmed,
                    "fPort": f_port,
                    "data": data.hex()  # Convertir bytes en hex string
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/devices/{dev_eui}/queue",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur lors de l'envoi de la commande: {str(e)}"
            )

    # ========================================================================
    # RÉCUPÉRATION D'INFORMATIONS DEPUIS CHIRPSTACK
    # ========================================================================

    async def get_device_info(self, dev_eui: str) -> Dict[str, Any]:
        """
        Récupérer les informations d'un device depuis ChirpStack

        Args:
            dev_eui: DevEUI du capteur

        Returns:
            Informations du device
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/devices/{dev_eui}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur lors de la communication avec ChirpStack: {str(e)}"
            )

    async def get_device_activation(self, dev_eui: str) -> Dict[str, Any]:
        """
        Récupérer les informations d'activation d'un device

        Args:
            dev_eui: DevEUI du capteur

        Returns:
            Informations d'activation (DevAddr, AppSKey, NwkSKey, etc.)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/devices/{dev_eui}/activation",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur lors de la récupération de l'activation: {str(e)}"
            )

    async def list_devices(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lister tous les devices de l'application ChirpStack

        Args:
            limit: Nombre maximum de devices à récupérer

        Returns:
            Liste des devices
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/applications/{self.application_id}/devices",
                    headers=self.headers,
                    params={"limit": limit},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("result", [])
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur lors de la récupération des devices: {str(e)}"
            )

    async def sync_devices(self, db: Session) -> Dict[str, Any]:
        """
        Synchroniser les devices de ChirpStack avec la base de données

        Returns:
            Statistiques de synchronisation
        """
        try:
            devices = await self.list_devices()

            stats = {
                "total": len(devices),
                "synced": 0,
                "errors": 0
            }

            for device in devices:
                try:
                    dev_eui = device.get("devEUI")
                    capteur = db.query(Capteur).filter(Capteur.dev_eui == dev_eui).first()

                    if capteur:
                        # Mettre à jour les informations
                        capteur.nom = device.get("name", capteur.nom)
                        capteur.description = device.get("description", capteur.description)
                        stats["synced"] += 1

                except Exception as e:
                    stats["errors"] += 1
                    print(f"Erreur lors de la sync du device {device.get('devEUI')}: {e}")
                    continue

            db.commit()
            return stats

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur lors de la synchronisation: {str(e)}"
            )

    # ========================================================================
    # FONCTIONS UTILITAIRES
    # ========================================================================

    def _calculate_battery_level(self, voltage: Optional[float]) -> Optional[int]:
        """
        Calculer le niveau de batterie en pourcentage à partir de la tension

        Basé sur une batterie 3.7V Li-ion typique:
        - 4.2V = 100%
        - 3.7V = 50%
        - 3.0V = 0%
        """
        if voltage is None:
            return None

        if voltage >= 4.2:
            return 100
        elif voltage <= 3.0:
            return 0
        else:
            # Interpolation linéaire
            return int(((voltage - 3.0) / (4.2 - 3.0)) * 100)

    def _calculate_signal_quality(
        self,
        rssi: Optional[int],
        snr: Optional[float]
    ) -> Optional[int]:
        """
        Calculer la qualité du signal en pourcentage

        Basé sur RSSI et SNR typiques pour LoRaWAN:
        - RSSI > -50 dBm: Excellent
        - RSSI -50 to -100 dBm: Bon à Moyen
        - RSSI < -100 dBm: Faible
        """
        if rssi is None:
            return None

        if rssi >= -50:
            return 100
        elif rssi <= -120:
            return 0
        else:
            # Interpolation linéaire
            return int(((rssi + 120) / 70) * 100)


# Instance globale du service
chirpstack_service = ChirpStackService()
