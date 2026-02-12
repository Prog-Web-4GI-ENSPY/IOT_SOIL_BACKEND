import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/chirpstack/chirpstack"

def send_payload(text):
    payload = {
        "devEUI": "yv66vtJ8i0Y=", # CAFEBABED27C8B46
        "publishedAt": "2026-02-11T14:45:00.000000Z",
        "objectJSON": json.dumps({"text": text})
    }
    response = requests.post(f"{BASE_URL}/?event=up", json=payload)
    print(f"Sent: {text}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

# Scenario 1: Initial record (ph, temperature, humidity)
# s:3 (ph), s:2 (temp), s:1 (hum)
print("\n--- Sending Payload 1 (PH, Temp, Hum) ---")
send_payload("d:100 s:3 p:1,d:1500 s:2 p:1,d:5500 s:1 p:1,")

# Scenario 2: Merge compatible data (NPK)
# s:4 (azote), s:5 (phosphore), s:6 (potassium)
print("\n--- Sending Payload 2 (NPK) - Should Merge ---")
send_payload("d:1000 s:4 p:1,d:1500 s:5 p:1,d:2000 s:6 p:1,")

# Scenario 3: New cycle (PH, Temp, Hum) - Should NOT Merge (overlap)
print("\n--- Sending Payload 3 (PH, Temp, Hum) - Should Create New Record ---")
send_payload("d:800 s:3 p:1,d:2600 s:2 p:1,d:4600 s:1 p:1,")
