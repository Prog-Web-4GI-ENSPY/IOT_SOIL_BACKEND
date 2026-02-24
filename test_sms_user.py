import asyncio
from app.services.infobip_service import InfobipService

async def main():
    service = InfobipService()
    print("Testing SMS sending to user's number via Infobip...")
    res = await service.send_sms("+237694773472", "Test message to verify Delivery")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
