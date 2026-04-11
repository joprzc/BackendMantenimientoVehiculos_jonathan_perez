import os, requests

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_DEBUG_TO = os.getenv("WHATSAPP_DEBUG_TO")  # usar en DEBUG


def send_whatsapp(to_number: str, body: str):
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID):
        return False, "Token/Phone ID no configurados"
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "text": {"body": body[:1000]},
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=8)
        if r.status_code == 200:
            return True, "Enviado"
        return False, f"Error API {r.status_code}: {r.text}"
    except requests.RequestException as exc:
        return False, f"Error red: {exc}"
