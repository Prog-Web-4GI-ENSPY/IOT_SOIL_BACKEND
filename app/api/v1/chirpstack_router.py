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
    """
    # 1. Extraction du contenu (Support objectJSON stringified ou object dict)
    content = payload.get("content")
    
    if not content and "objectJSON" in payload:
        try:
            # ChirpStack v4+ peut envoyer un string JSON dans objectJSON
            obj_json = payload.get("objectJSON")
            if isinstance(obj_json, str):
                import json
                obj = json.loads(obj_json)
                content = obj.get("text") or obj.get("content")
        except Exception as e:
            print(f"Erreur decoding objectJSON: {e}")

    # Fallback: object dict standard
    if not content and "object" in payload and isinstance(payload["object"], dict):
        content = payload["object"].get("content")
        
    if content:
        content = str(content).strip()
    else:
        content = ""

    if not content:
        print(f"PAYLOAD DEBUG: {payload}")
        raise HTTPException(status_code=400, detail="Le contenu est vide (champs 'content', 'objectJSON' ou 'object' manquants)")

    # 2. Parsing des segments
    # Le format peut utiliser ',' ou ';' comme séparateur de mesures
    # Exemple: "d:800 s:1 p:1;d:0 s:2 p:1;"
    if ";" in content and "," not in content:
        delimiter = ";"
    else:
        delimiter = ","

    segments = [s.strip() for s in content.split(delimiter) if s.strip()]
    
    aggregated_data = {}
    # 1:hum, 2:temp, 3:ph, 4:n, 5:p, 6:k
    mapping = {1: "humidity", 2: "temperature", 3: "ph", 4: "azote", 5: "phosphore", 6: "potassium"}

    try:
        for seg in segments:
            # seg ex: "d:800 s:1 p:1"
            parts = [p for p in seg.split(" ") if p]
            
            if len(parts) < 3:
                continue

            # Extraction d:valeur
            # parts[0] -> "d:800"
            valeur = float(parts[0].split(":")[1])/100
            
            # Extraction s:code;indice
            # parts[1] -> "s:1" ou "s:code;indice"
            sensor_info = parts[1].split(":")[1] # "1" ou "code;indice"
            
            if ";" in sensor_info:
                capteur_code, indice_str = sensor_info.split(";")
                indice = int(indice_str)
            else:
                # Si pas d'indice, on suppose que c'est le code.
                # Mais quel indice ? 
                # PROVISOIRE: On essaie de déduire ou on utilise une valeur par défaut ?
                # Si le format est "s:1", c'est peut-être code=1.
                # Sans indice, mapping impossible -> On skip ou default ?
                # D'après le mapping (1=hum, 2=temp...), l'indice EST le type.
                # Si 's:1' implique le type est 1 ??
                # Hypothèse: sensor_code IS the index? Non, code est string.
                # On va tenter d'utiliser le code comme 'indice' si c'est un digit et qu'on a pas d'autre info?
                # Ou alors on loggue une erreur.
                # Pour le test utilisateur "s:1", si 1 est le code capteur, il manque le type de mesure.
                # C'est bloquant.
                # SAUF si le user a dit "le capteur cap1 et la parcelle 1 existe".
                # Ici on a "s:1".
                # On va assumer capteur_code = sensor_info.
                # Indice ???
                capteur_code = sensor_info
                # Hack / Heustistique: Si pas d'indice, on ne peut pas mapper la valeur.
                # On va hardcoder indice=1 (humidity) pour tester ou failer soft ?
                # Mieux: Skip warning.
                print(f"WARNING: Segment '{seg}' sans indice de mesure (format s:code;indice attendu). Ignoré.")
                continue
            
            # Extraction p:code
            # parts[2] -> "p:1"
            parcelle_raw = parts[2].split(":")
            if len(parcelle_raw) > 1:
                parcelle_code = parcelle_raw[1]
            else:
                 # Fallback si mal formé
                 continue

            key = (capteur_code, parcelle_code)
            if key not in aggregated_data:
                aggregated_data[key] = {"metrics": {}}
            
            if indice in mapping:
                aggregated_data[key]["metrics"][mapping[indice]] = valeur

        created_records = []
        for (c_code, p_code), data in aggregated_data.items():
            # 1. Vérification de l'existence du capteur
            capteur = db.query(Capteur).filter(Capteur.code == c_code).first()
            if not capteur:
                print(f"Capteur inconnu: {c_code}")
                # On continue au lieu de raise 404 pour ne pas bloquer tout le batch
                continue 

            # 2. Vérification de l'existence de la parcelle
            parcelle = db.query(Parcelle).filter(Parcelle.code == p_code).first()
            if not parcelle:
                print(f"Parcelle inconnue: {p_code}")
                continue

            # 3. Si les deux existent, on crée l'enregistrement
            new_meas = SensorMeasurements(
                id=str(uuid.uuid4()),
                capteur_id=capteur.id,
                parcelle_id=parcelle.id,
                timestamp=datetime.utcnow(),
                humidity=data["metrics"].get("humidity"),
                temperature=data["metrics"].get("temperature"),
                ph=data["metrics"].get("ph"),
                azote=data["metrics"].get("azote"),
                phosphore=data["metrics"].get("phosphore"),
                potassium=data["metrics"].get("potassium"),
                measurements=data["metrics"]
            )
            db.add(new_meas)
            created_records.append(new_meas)

        db.commit()
        return {
            "status": "success", 
            "records_created": len(created_records)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"ERROR EXCEPTION: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur de formatage: {str(e)}")

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