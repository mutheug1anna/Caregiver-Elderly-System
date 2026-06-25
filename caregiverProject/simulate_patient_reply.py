import requests

# This points directly to your local Django webhook url
URL = "http://127.0.0.1:8000/at-webhook/"

# This data dictionary copies EXACTLY what Africa's Talking sends 
# when a patient types '1' and hits send.
DATA_PAYLOAD = {
    'from': '+254712345678',  # ⚠️ CHANGE THIS to your test patient's phone number
    'text': '1'               # This mimics the user typing '1' (Taken)
}

print("🚀 Sending fake patient reply to Django server...")
try:
    response = requests.post(URL, data=DATA_PAYLOAD)
    print(f"📡 Server Response Code: {response.status_code}")
    print(f"💬 Server Says: {response.text}")
except Exception as e:
    print(f" Failed to reach server: {e}")