from twilio.rest import Client
from django.conf import settings


def enviar_whatsapp(numero, mensaje):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=mensaje,
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{numero}",
        )
        return True
    except Exception as e:
        print(f"Error al enviar WhatsApp: {e}")
        return False
