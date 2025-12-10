"""
Service pour l'intégration avec ChirpStack
Gère la récupération et le traitement des données des capteurs LoRaWAN
"""
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.capteur import Capteur, StatutCapteur
from app.models.sensor_data import SensorMeasurements
from app.services.capteur_service import capteur_service


class ChirpStackService:
    """Service pour interagir avec ChirpStack"""

    def __init__(self):
        self.api_url = str(settings.CHIRPSTACK_API_URL)
        self.api_token = settings.CHIRPSTACK_API_TOKEN
        self.application_id = settings.CHIRPSTACK_APPLICATION_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

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

    async def get_device_data(
        self,
        dev_eui: str,
        limit: int = 100,
        start_timestamp: Optional[datetime] = None,
        end_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupérer l'historique des données d'un device

        Args:
            dev_eui: DevEUI du capteur
            limit: Nombre maximum de mesures à récupérer
            start_timestamp: Date de début
            end_timestamp: Date de fin

        Returns:
            Liste des mesures
        """
        try:
            params = {
                "limit": limit
            }

            if start_timestamp:
                params["startTimestamp"] = start_timestamp.isoformat()

            if end_timestamp:
                params["endTimestamp"] = end_timestamp.isoformat()

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/devices/{dev_eui}/events",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("result", [])
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur lors de la récupération des données: {str(e)}"
            )

    async def process_uplink_data(
        self,
        db: Session,
        uplink_data: Dict[str, Any]
    ) -> SensorMeasurements:
        """
        Traiter les données uplink reçues de ChirpStack via webhook

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
            capteur = capteur_service.get_capteur_by_dev_eui(db, dev_eui)

            if not capteur:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Capteur avec DevEUI {dev_eui} non trouvé"
                )

            # Extraire les métadonnées
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
            capteur_service.update_capteur_status(
                db=db,
                capteur_id=str(capteur.id),
                statut=StatutCapteur.ONLINE,
                last_seen=datetime.utcnow(),
                battery_level=self._calculate_battery_level(
                    data.get("batteryVoltage") or data.get("battery_voltage")
                ),
                signal_quality=self._calculate_signal_quality(
                    rx_info.get("rssi"),
                    rx_info.get("loRaSNR")
                )
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

    async def sync_devices(self, db: Session) -> Dict[str, Any]:
        """
        Synchroniser tous les devices de l'application ChirpStack avec la base de données

        Returns:
            Statistiques de synchronisation
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/applications/{self.application_id}/devices",
                    headers=self.headers,
                    params={"limit": 1000},
                    timeout=30.0
                )
                response.raise_for_status()
                devices = response.json().get("result", [])

            stats = {
                "total": len(devices),
                "synced": 0,
                "errors": 0
            }

            for device in devices:
                try:
                    dev_eui = device.get("devEUI")
                    capteur = capteur_service.get_capteur_by_dev_eui(db, dev_eui)

                    if capteur:
                        # Mettre à jour les informations
                        capteur.nom = device.get("name", capteur.nom)
                        capteur.description = device.get("description", capteur.description)
                        db.commit()
                        stats["synced"] += 1

                except Exception as e:
                    stats["errors"] += 1
                    print(f"Erreur lors de la sync du device {device.get('devEUI')}: {e}")
                    continue

            return stats

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Erreur lors de la synchronisation: {str(e)}"
            )


chirpstack_service = ChirpStackService()
