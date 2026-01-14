import requests
import json

# URL of the local API (assuming default port 8000)
url = "http://localhost:8000/api/v1/chirpstack/chirpstack/?event=up"

# Valid data provided by user: capteur=cap1, parcelle=1
# Format expected: d:valeur s:code;indice p:code
# Mocking humidity (indice 1)
content_str = "d:4500 s:cap1;1 p:1"

payload = {
    "applicationID": "1",
    "applicationName": "test-app",
    "deviceName": "test-device",
    "devEUI": "0000000000000000",
    "object": {
        "text": content_str
    }
}

try:
    print(f"Sending POST request to {url} with content: '{content_str}'...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    if response.status_code == 200 or response.status_code == 201:
        print("SUCCESS: Full flow worked!")
        exit(0)
    else:
        print(f"FAIL: Unexpected status code {response.status_code}")
        exit(1)

except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to localhost:8000. Is the server running?")
    exit(1)
