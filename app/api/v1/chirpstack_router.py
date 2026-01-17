"""
Router pour les webhooks ChirpStack
"""
from fastapi import APIRouter, Depends, status, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
from datetime import datetime

from app.database import get_db
from app.models.sensor_data import SensorMeasurements
from app.models.capteur import Capteur
from app.models.parcelle import Parcelle
from app.models.cap_parcelle import CapParcelle
from sqlalchemy import or_
import base64
import json

router = APIRouter(
    prefix="/chirpstack",
    tags=["ChirpStack"]
)

@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Webhook ChirpStack pour les événements (up, join, etc.)"
)
async def handle_chirpstack_webhook(
    event: str = Query(...),
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Point d'entrée principal pour les webhooks ChirpStack.
    Dispatche vers la fonction appropriée selon le paramètre 'event'.
    """
    if event == "up":
        return await handle_up_event(payload, db)
    elif event == "join":
        return handle_join_event(payload)
    else:
        # On log ou on ignore les autres événements
        print(f"Événement non géré: {event}")
        return {"status": "ignored", "event": event}

async def handle_up_event(payload: Dict[str, Any], db: Session):
    """
    Traite l'événement 'up' (Uplink) contenant les données des capteurs.
    Identification par DevEUI et historique d'assignation CapParcelle.
    """
    try:
        # 1. Identification du Device (Capteur) via DevEUI
        dev_eui_raw = payload.get("devEUI")
        if not dev_eui_raw:
            print(f"PAYLOAD DEBUG: {payload}")
            raise HTTPException(status_code=400, detail="devEUI manquant dans le payload")

        # Conversion Base64 -> Hex si nécessaire
        try:
            # Si contient des caractères non-hex ou longueur != 16 (hex)
            if not all(c in "0123456789ABCDEFabcdef" for c in dev_eui_raw) or len(dev_eui_raw) != 16:
                decoded = base64.b64decode(dev_eui_raw).hex().upper()
                dev_eui = decoded
            else:
                dev_eui = dev_eui_raw.upper()
        except Exception:
            dev_eui = dev_eui_raw.upper()

        capteur = db.query(Capteur).filter(Capteur.dev_eui == dev_eui).first()
        if not capteur:
            raise HTTPException(status_code=404, detail=f"Capteur avec DevEUI {dev_eui} inconnu")

        # 2. Identification du Temps et de la Parcelle correspondante
        published_at_str = payload.get("publishedAt")
        if published_at_str:
            try:
                # Nettoyage pour fromisoformat (ex: 2026-01-16T11:53:07.799444068Z)
                dt_str = published_at_str.replace('Z', '').replace(' ', 'T')
                if '.' in dt_str:
                    base, micros = dt_str.split('.')
                    dt_str = f"{base}.{micros[:6]}"
                event_time = datetime.fromisoformat(dt_str)
            except Exception as e:
                print(f"Erreur parsing date {published_at_str}: {e}")
                event_time = datetime.utcnow()
        else:
            event_time = datetime.utcnow()

        # Recherche de l'assignation active au moment 'event_time'
        assignment = db.query(CapParcelle).filter(
            CapParcelle.capteur_id == capteur.id,
            CapParcelle.date_assignation <= event_time
        ).filter(
            or_(
                CapParcelle.date_desassignation == None,
                CapParcelle.date_desassignation >= event_time
            )
        ).order_by(CapParcelle.date_assignation.desc()).first()

        if not assignment:
            raise HTTPException(
                status_code=400, 
                detail=f"Capteur {capteur.code} n'était assigné à aucune parcelle le {event_time}"
            )

        parcelle_id = assignment.parcelle_id

        # 3. Extraction du contenu des mesures (segments)
        content = payload.get("content")
        if not content and "objectJSON" in payload:
            try:
                obj_json = payload.get("objectJSON")
                if isinstance(obj_json, str):
                    obj = json.loads(obj_json)
                    content = obj.get("text") or obj.get("content")
            except Exception:
                pass

        if not content and "object" in payload and isinstance(payload["object"], dict):
            content = payload["object"].get("content")
            
        if content:
            content = str(content).strip()
        else:
            content = ""

        if not content:
            raise HTTPException(status_code=400, detail="Contenu des mesures manquant")

        # Parsing des segments (format: "d:valeur s:code;indice p:parcelle_code")
        delimiter = ";" if ";" in content and "," not in content else ","
        segments = [s.strip() for s in content.split(delimiter) if s.strip()]
        
        metrics = {}
        # Mapping indices: 1:hum, 2:temp, 3:ph, 4:n, 5:p, 6:k
        mapping = {1: "humidity", 2: "temperature", 3: "ph", 4: "azote", 5: "phosphore", 6: "potassium"}

        for seg in segments:
            parts = [p for p in seg.split(" ") if p]
            if len(parts) < 2: continue

            try:
                # Valeur (d:X)
                valeur = float(parts[0].split(":")[1]) / 100
                
                # Capteur Info (s:code;indice)
                sensor_info = parts[1].split(":")[1]
                if ";" in sensor_info:
                    _, indice_str = sensor_info.split(";")
                    indice = int(indice_str)
                    if indice in mapping:
                        metrics[mapping[indice]] = valeur
            except (IndexError, ValueError):
                continue

        if not metrics:
            return {"status": "success", "message": "Aucune mesure valide extraite", "records_created": 0}

        # 4. Création de l'enregistrement unique pour cet uplink
        new_meas = SensorMeasurements(
            id=str(uuid.uuid4()),
            capteur_id=capteur.id,
            parcelle_id=parcelle_id,
            timestamp=event_time,
            humidity=metrics.get("humidity"),
            temperature=metrics.get("temperature"),
            ph=metrics.get("ph"),
            azote=metrics.get("azote"),
            phosphore=metrics.get("phosphore"),
            potassium=metrics.get("potassium"),
            measurements=metrics
        )
        db.add(new_meas)
        db.commit()

        return {
            "status": "success",
            "records_created": 1,
            "capteur": capteur.code,
            "parcelle_id": parcelle_id,
            "timestamp": event_time.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"ERROR EXCEPTION: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur de traitement des données: {str(e)}")

def handle_join_event(payload: Dict[str, Any]):
    """
    Traite l'événement 'join'.
    Affiche simplement les infos dans la console pour l'instant.
    """
    dev_eui = payload.get("devEUI", "Unknown")
    dev_addr = payload.get("devAddr", "Unknown")
    
    # Try to find info in device_info or other common ChirpStack fields if available
    # For now strictly following the User Request print style
    # "Device: %s joined with DevAddr: %s"
    
    # ChirpStack JSON usually has devEUI at root or in device_info
    
    print(f"Device: {dev_eui} joined with DevAddr: {dev_addr}")
    return {"status": "joined", "devEUI": dev_eui}