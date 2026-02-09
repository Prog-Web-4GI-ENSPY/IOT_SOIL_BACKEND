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

        # 2. Identification du Temps
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
        
        parcelle_id = None
        extracted_parcelle_code = None

        for seg in segments:
            parts = [p for p in seg.split(" ") if p]
            if len(parts) < 2: continue

            try:
                # Valeur (d:X)
                valeur = float(parts[0].split(":")[1]) / 100
                
                # Capteur Info (s:indice)
                sensor_info = parts[1].split(":")[1]
                indice = int(sensor_info)
                if indice in mapping:
                    metrics[mapping[indice]] = valeur
                
                # Parcelle Info (p:parcelle_code) - if present in this segment
                for part in parts:
                    if part.startswith("p:"):
                        extracted_parcelle_code = part.split(":")[1]
                        break

            except (IndexError, ValueError):
                continue

        if not metrics:
            return {"status": "success", "message": "Aucune mesure valide extraite", "records_created": 0}

        # 4. Identification de la Parcelle via parcelle_code
        if not extracted_parcelle_code:
            # Fallback si absent du payload mais requis
            raise HTTPException(status_code=400, detail="Code parcelle (p:XXX) manquant dans le contenu")

        parcelle = db.query(Parcelle).filter(Parcelle.code == extracted_parcelle_code).first()
        if not parcelle:
            raise HTTPException(status_code=404, detail=f"Parcelle avec le code {extracted_parcelle_code} non trouvée")
        
        parcelle_id = parcelle.id

        # 5. Création de l'enregistrement unique pour cet uplink
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
            "parcelle": extracted_parcelle_code,
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