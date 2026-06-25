import requests

URL = "http://127.0.0.1:8000/at-webhook/"

DATA_PAYLOAD = {
    'from': '+254778902116',  
    'text': '1'
}

print("🚀 Simulating patient reply of '1'...")
response = requests.post(URL, data=DATA_PAYLOAD)
print(f"📡 Server Response: {response.status_code}")
print(f"💬 Server Says: {response.text}")