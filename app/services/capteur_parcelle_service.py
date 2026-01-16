from sqlalchemy.orm import Session
from app.models.capteur import Capteur
from app.models.parcelle import Parcelle
from app.models.cap_parcelle import CapParcelle
from datetime import datetime
from fastapi import HTTPException, status

def assign_capteur_to_parcelle(db: Session, code_parcelle: str, code_capteur: str):
    # Rechercher la parcelle
    parcelle = db.query(Parcelle).filter(Parcelle.code == code_parcelle).first()
    if not parcelle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Parcelle avec le code {code_parcelle} non trouvée")

    # Rechercher le capteur
    capteur = db.query(Capteur).filter(Capteur.code == code_capteur).first()
    if not capteur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capteur avec le code {code_capteur} non trouvé")

    # Vérifier si le capteur est déjà assigné (pas de date de désassignation)
    active_assignment = db.query(CapParcelle).filter(
        CapParcelle.capteur_id == capteur.id,
        CapParcelle.date_desassignation == None
    ).first()
    
    if active_assignment:
        if active_assignment.parcelle_id == parcelle.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le capteur est déjà assigné à cette parcelle")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le capteur est déjà assigné à une autre parcelle. Veuillez le désassigner d'abord.")

    # Créer l'assignation
    new_assignment = CapParcelle(
        capteur_id=capteur.id,
        parcelle_id=parcelle.id,
        date_assignation=datetime.utcnow()
    )
    
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    return new_assignment

def desassign_capteur_de_parcelle(db: Session, code_parcelle: str, code_capteur: str):
    # Rechercher la parcelle
    parcelle = db.query(Parcelle).filter(Parcelle.code == code_parcelle).first()
    if not parcelle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Parcelle avec le code {code_parcelle} non trouvée")

    # Rechercher le capteur
    capteur = db.query(Capteur).filter(Capteur.code == code_capteur).first()
    if not capteur:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capteur avec le code {code_capteur} non trouvé")

    # Trouver l'assignation active
    assignment = db.query(CapParcelle).filter(
        CapParcelle.capteur_id == capteur.id,
        CapParcelle.parcelle_id == parcelle.id,
        CapParcelle.date_desassignation == None
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucune assignation active trouvée pour ce couple capteur/parcelle")

    # Mettre à jour la date de désassignation
    assignment.date_desassignation = datetime.utcnow()
    db.commit()
    db.refresh(assignment)
    
    return assignment
