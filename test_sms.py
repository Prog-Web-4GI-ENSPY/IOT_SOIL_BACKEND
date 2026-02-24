import asyncio
from app.services.infobip_service import InfobipService
from app.database import get_db
from app.models.user import User

async def main():
    service = InfobipService()
    db = next(get_db())
    users = db.query(User).all()
    print("ALL USERS:")
    for u in users:
        print(f"ID={u.id} Email={u.email} Tel={u.telephone} Modes={u.notification_modes}")
    
    print("\nTesting SMS sending via Infobip...")
    # NOTE: we'll use a dummy number to just see the raw response or exception
    res = await service.send_sms("+237694773472", "Test message from debug script")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
