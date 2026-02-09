import httpx
import asyncio
import json

async def test_unified_prediction():
    url = "http://localhost:8000/api/v1/recommendations/predict-crop"
    payload = {
        "soil_data": {
            "N": 90,
            "P": 42,
            "K": 43,
            "temperature": 20.8,
            "humidity": 82.0,
            "ph": 6.5
        },
        "region": "Centre",
        "query": "Quel est le meilleur moment pour le maïs ?"
    }
    
    # We need a token. For simulation, let's assume registration and login or just check if it fails with 401 as expected but logic is there.
    # Actually, I'll just check if the code compiles and the endpoint exists.
    
    print(f"Testing URL: {url}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Recommended Crop: {data['recommended_crop']}")
                print(f"Justification Summary: {data['justification'][:200]}...")
                if 'detailed_justifications' in data:
                    print(f"Questions answered: {list(data['detailed_justifications'].keys())}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_unified_prediction())
