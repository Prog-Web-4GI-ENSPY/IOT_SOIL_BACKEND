import requests
import json
import uuid

# URL of the local API (assuming default port 8000)
url = "http://localhost:8000/api/v1/chirpstack/chirpstack/?event=up"

# Simulated ChirpStack payload with nested object
payload = {
    "applicationID": "1",
    "applicationName": "test-app",
    "deviceName": "test-device",
    "devEUI": "0000000000000000",
    "object": {
        "text": "d:2500 s:abc;1 p:xyz, d:123 s:abc;2 p:xyz"
    }
}

try:
    print(f"Sending POST request to {url}...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    if response.status_code == 422:
        print("FAIL: Still getting 422 Unprocessable Entity")
        exit(1)
    elif response.status_code in [200, 201, 404, 400]:
        # 404/400 are acceptable here because the sensor/parcelle codes don't exist in DB
        # The goal is essentially to pass the validation layer.
        print("SUCCESS: Passed validation layer (422 avoided)")
        exit(0)
    else:
        print(f"UNKNOWN: Unexpected status code {response.status_code}")
        exit(1)

except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to localhost:8000. Is the server running?")
    exit(1)
