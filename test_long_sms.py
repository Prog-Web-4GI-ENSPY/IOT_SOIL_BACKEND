import asyncio
from app.services.infobip_service import InfobipService

async def main():
    service = InfobipService()
    print("Testing LONG SMS sending to user's number via Infobip...")
    long_msg = "A" * 1600 # Very long message
    res = await service.send_sms("+237694773472", long_msg)
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
