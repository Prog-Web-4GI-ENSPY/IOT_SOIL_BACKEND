import pytest
from datetime import datetime
from fastapi.testclient import TestClient


def test_chirpstack_webhook(client: TestClient, test_parcelle, db):
    """Test du webhook ChirpStack"""
    from app.models.capteur import Capteur, TypeCapteur
    
    # Créer un capteur
    capteur = Capteur(
        nom="Capteur Webhook",
        code="WEBHOOK-001",
        type_capteur=TypeCapteur.HUMIDITE_SOL,
        modele="Model X",
        dev_eui="0123456789ABCDEF",
        application_id="app-001",
        parcelle_id=test_parcelle.id,
        latitude=3.8505,
        longitude=11.5035,
        date_installation="2024-01-01T00:00:00"
    )
    db.add(capteur)
    db.commit()
    
    # Simuler un message ChirpStack
    response = client.post(
        "/api/v1/sensor-data/webhook/chirpstack",
        json={
            "applicationID": "app-001",
            "applicationName": "AgroPredict",
            "deviceName": "Capteur Webhook",
            "devEUI": "0123456789ABCDEF",
            "rxInfo": [
                {
                    "gatewayID": "gateway-001",
                    "uplinkID": "12345",
                    "rssi": -85,
                    "snr": 8.5,
                    "channel": 0,
                    "rfChain": 0
                }
            ],
            "txInfo": {
                "frequency": 868100000,
                "modulation": "LORA",
                "loRaModulationInfo": {
                    "bandwidth": 125,
                    "spreadingFactor": 7,
                    "codeRate": "4/5"
                }
            },
            "fCnt": 42,
            "fPort": 1,
            "data": "01234567",  # Payload en base64
            "object": {
                "temperature": 25.5,
                "soilMoisture": 65.0
            },
            "timestamp": "2024-01-15T10:30:00Z"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"


def test_get_sensor_data(client: TestClient, auth_headers, test_parcelle, db):
    """Test de récupération des données capteur"""
    from app.models.capteur import Capteur, TypeCapteur
    from app.models.sensor_data import DonneeCapteur
    
    # Créer un capteur
    capteur = Capteur(
        nom="Capteur Data",
        code="DATA-001",
        type_capteur=TypeCapteur.HUMIDITE_SOL,
        modele="Model X",
        dev_eui="0123456789ABCDEF",
        application_id="app-001",
        parcelle_id=test_parcelle.id,
        latitude=3.8505,
        longitude=11.5035,
        date_installation="2024-01-01T00:00:00"
    )
    db.add(capteur)
    db.commit()
    db.refresh(capteur)
    
    # Créer des données
    for i in range(10):
        donnee = DonneeCapteur(
            capteur_id=capteur.id,
            timestamp=datetime.utcnow(),
            dev_eui=capteur.dev_eui,
            f_port=1,
            f_cnt=i,
            decoded_data={
                "temperature": 25.0 + i,
                "soilMoisture": 60.0 + i
            },
            is_valid=True
        )
        db.add(donnee)
    db.commit()
    
    response = client.get(
        f"/api/v1/capteurs/{capteur.id}/data",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["pagination"]["total"] == 10