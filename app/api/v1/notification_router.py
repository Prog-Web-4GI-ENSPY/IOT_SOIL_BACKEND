from fastapi import APIRouter, Depends, HTTPException, Body
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationTestRequest, NotificationResponse
from app.routers.auth_router import get_current_user
from app.models.user import User, NotificationMode
from typing import List

router = APIRouter()

@router.post("/test", response_model=NotificationResponse, summary="Tester l'envoi d'une notification")
async def test_notification(
    request: NotificationTestRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Permet de tester l'envoi d'une notification sur un canal spécifique.
    Si 'target' n'est pas fourni, utilise les informations du profil de l'utilisateur.
    """
    notif_service = NotificationService()
    target = request.target
    
    try:
        if request.mode == NotificationMode.EMAIL:
            target = target or current_user.email
            res = await notif_service.send_email(target, "Test AgroPredict", request.message)
            if not res.get("success"):
                raise Exception(res.get("error", "Erreur inconnue"))
        
        elif request.mode == NotificationMode.SMS:
            target = target or current_user.telephone
            if not target:
                raise HTTPException(status_code=400, detail="Numéro de téléphone non configuré")
            res = await notif_service.send_sms(target, request.message)
            if not res.get("success"):
                raise Exception(res.get("error", "Erreur inconnue"))
            
        elif request.mode == NotificationMode.WHATSAPP:
            target = target or current_user.telephone
            if not target:
                raise HTTPException(status_code=400, detail="Numéro de téléphone non configuré")
            res = await notif_service.send_whatsapp(target, request.message)
            if not res.get("success"):
                raise Exception(res.get("error", "Erreur inconnue"))
            
        elif request.mode == NotificationMode.TELEGRAM:
            # Pour Telegram, on assume que target est le chat_id ou on utilise un defaut configuré
            res = await notif_service.send_telegram(request.message, chat_id=target)
            if not res.get("success"):
                raise Exception(res.get("error", "Erreur inconnue"))
            
        return NotificationResponse(
            success=True,
            message=f"Notification envoyée via {request.mode} à {target}"
        )
    except Exception as e:
        return NotificationResponse(
            success=False,
            message=f"Échec de l'envoi via {request.mode}",
            details={"error": str(e)}
        )

@router.get("/modes", response_model=List[str], summary="Liste des modes de notification supportés")
async def get_supported_modes():
    """Retourne la liste des canaux de communication disponibles."""
    return [mode.value for mode in NotificationMode]
