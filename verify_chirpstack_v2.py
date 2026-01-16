import sys
import os
import json
from datetime import datetime, timedelta
import uuid

# Configuration du chemin pour importer l'app
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.capteur import Capteur, StatutCapteur
from app.models.parcelle import Parcelle, TypeSol
from app.models.cap_parcelle import CapParcelle
from app.models.terrain import Terrain, TypeTerrain, StatutTerrain
from app.models.location import Localite, Continent, ClimateZone
from app.models.sensor_data import SensorMeasurements
from app.models.user import User
import base64

def setup_test_data(db: Session):
    # Nettoyage des tests précédents
    dev_eui_b64 = "yv66vtJ8i0Y="
    dev_eui_hex = base64.b64decode(dev_eui_b64).hex().upper()
    
    old_cap = db.query(Capteur).filter(Capteur.dev_eui == dev_eui_hex).first()
    if old_cap:
        db.query(CapParcelle).filter(CapParcelle.capteur_id == old_cap.id).delete()
        db.query(SensorMeasurements).filter(SensorMeasurements.capteur_id == old_cap.id).delete()
        db.delete(old_cap)
    
    db.commit()

    # 0. Créer un utilisateur
    user = User(
        id=str(uuid.uuid4()),
        nom="Test",
        prenom="User",
        email=f"test_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="fakehash"
    )
    db.add(user)
    db.flush()

    # 1. Créer une localité et un terrain
    localite = Localite(
        nom="Test Localite",
        latitude=0.0,
        longitude=0.0,
        ville="Test",
        pays="Test",
        continent=Continent.AFRIQUE,
        timezone="UTC",
        superficie=1.0,  # km²
        climate_zone=ClimateZone.TROPICAL
    )
    db.add(localite)
    db.flush()

    terrain = Terrain(
        nom="Test Terrain",
        type_terrain=TypeTerrain.AGRICOLE,
        statut=StatutTerrain.ACTIF,
        localite_id=localite.id,
        latitude=0.0,
        longitude=0.0,
        superficie_totale=10.0,
        user_id=user.id
    )
    db.add(terrain)
    db.flush()

    # 2. Créer une parcelle
    p_code = f"P-ALPHA-{uuid.uuid4().hex[:6]}"
    parcelle = Parcelle(
        nom="Parcelle Alpha",
        code=p_code,
        terrain_id=terrain.id,
        superficie=1.0,
        type_sol=TypeSol.ARGILEUX
    )
    db.add(parcelle)
    db.flush()

    # 3. Créer un capteur avec le DevEUI du message
    # yv66vtJ8i0Y= en base64 -> CAFEBABED27C8B46 en hex
    dev_eui_b64 = "yv66vtJ8i0Y="
    dev_eui_hex = base64.b64decode(dev_eui_b64).hex().upper()
    print(f"DevEUI Hex: {dev_eui_hex}")

    c_code = f"cap-test-{uuid.uuid4().hex[:6]}"
    capteur = Capteur(
        nom="Capteur Test",
        code=c_code,
        dev_eui=dev_eui_hex,
        date_installation=datetime.utcnow() - timedelta(days=10)
    )
    db.add(capteur)
    db.flush()

    # 4. Créer l'assignation historique
    # L'événement est du 2026-01-16T11:53:07
    # On met une assignation qui couvre cette date
    assignment = CapParcelle(
        capteur_id=capteur.id,
        parcelle_id=parcelle.id,
        date_assignation=datetime(2026, 1, 1, 0, 0, 0),
        date_desassignation=None
    )
    db.add(assignment)
    db.commit()
    
    return dev_eui_b64, parcelle.id, c_code

def verify_logic():
    db = SessionLocal()
    try:
        dev_eui_b64, expected_parcelle_id, c_code = setup_test_data(db)
        
        # Payload simulé
        payload = {
            "devEUI": dev_eui_b64,
            "publishedAt": "2026-01-16T11:53:07.799444068Z",
            "objectJSON": json.dumps({"text": "d:6700 s:cap1;2 p:1,d:6600 s:cap1;2 p:1,"})
        }
        
        # Simuler l'appel à handle_up_event
        from app.api.v1.chirpstack_router import handle_up_event
        import asyncio
        
        async def run_test():
            result = await handle_up_event(payload, db)
            print(f"Result: {result}")
            
            # Vérifier l'enregistrement créé
            capteur_id = db.query(Capteur).filter(Capteur.code == c_code).first().id
            meas = db.query(SensorMeasurements).filter(SensorMeasurements.capteur_id == capteur_id).first()
            print(f"Measurement Parcelle ID: {meas.parcelle_id}")
            print(f"Expected Parcelle ID: {expected_parcelle_id}")
            assert str(meas.parcelle_id) == str(expected_parcelle_id)
            assert meas.temperature == 66.0 # Le dernier segment d:6600 s:cap1;2
            print("Verification SUCCESSFUL!")

        asyncio.run(run_test())

    except Exception as e:
        print(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_logic()
