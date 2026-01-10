import requests

def send_sms(phone_number, message):
    """
    Send WhatsApp message via Notifier API using direct API key
    and an active Unofficial WhatsApp session.
    """

    API_KEY = "631c04ed-4553-4c70-9486-fb88aff356af"

    GATEWAY_IDENTIFIER = "0z8qNw7q-xpeFooTsFqOcA7-RUAtioDZ"

    # Notifier API endpoint
    url = "https://notifier.b-o-ss.com/api/whatsapp/send"

    # Message payload
    payload = {
        "contact": [
            {
                "number": phone_number,
                "message": message,
                "gateway_identifier": GATEWAY_IDENTIFIER
            }
        ]
    }

    headers = {
        "Api-key": API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print("Response Status Code:", response.status_code)
        print("Response Body:", response.text)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Message sent successfully!")
                return True
            else:
                print("❌ API Error:", data.get("message"))
        else:
            print("❌ Request failed:", response.status_code)

    except requests.RequestException as e:
        print(f"❌ Request Exception: {e}")

    return False
