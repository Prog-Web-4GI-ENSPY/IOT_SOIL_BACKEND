import requests
import json

def test_unified_prediction():
    url = "http://localhost:8000/api/v1/recommendations/predict-crop"
    
    # Données de sol typiques (exemple pour Rice selon le dataset habituel)
    payload = {
        "soil_data": {
            "N": 90,
            "P": 42,
            "K": 43,
            "temperature": 20.8,
            "humidity": 82.0,
            "ph": 6.5
        },
        "region": "Centre"
    }
    
    # Note: Ce test suppose que le serveur tourne localement sur le port 8000
    # et qu'il n'y a pas de protection auth bloquante pour ce endpoint si testé ainsi,
    # ou qu'on utilise un token valide.
    
    print(f"Testing endpoint: {url}")
    try:
        # On essaie d'appeler l'API sans auth pour voir si elle répond (même avec 401)
        # Mais l'idéal est de vérifier la structure de la réponse si possible.
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(f"Recommended Crop: {result['recommended_crop']}")
            print(f"Confidence Score: {result['confidence_score']}")
            print(f"Justification preview: {result['justification'][:100]}...")
        elif response.status_code == 401:
            print("Authentication required (expected if middleware is active).")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_unified_prediction()
