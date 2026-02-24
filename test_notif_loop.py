import asyncio
from app.services.notification_service import NotificationService
from app.database import get_db
from app.models.user import User

async def main():
    service = NotificationService()
    db = next(get_db())
    # Take user who has sms in modes
    user = db.query(User).filter(User.email == "azangueleonel9@gmail.com").first()
    
    print(f"User modes: {user.notification_modes}")
    print(f"User telephone: {user.telephone}")
    
    messages = [
        ("Titre de test", "Ceci est un test de notification AgroPredict en local.")
    ]
    
    for mode in user.notification_modes:
        print(f"--- Envoi via {mode} ---")
        for title, body in messages:
            try:
                if mode == 'email':
                    res = await service.send_email(user.email, title, body)
                    print(f"Email result: {res}")
                elif mode == 'sms' and user.telephone:
                    res = await service.send_sms(user.telephone, body)
                    print(f"SMS result: {res}")
                elif mode == 'whatsapp' and user.telephone:
                    res = await service.send_whatsapp(user.telephone, body)
                    print(f"WhatsApp result: {res}")
            except Exception as e:
                print(f"Error for mode {mode} with title '{title}': {e}")

if __name__ == "__main__":
    asyncio.run(main())
