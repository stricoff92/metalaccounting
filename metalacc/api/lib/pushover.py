from django.conf import settings
import requests

def send_admin_alert(message:str):

    if settings.ENV == 'TESTING':
        return

    data = {
        "token": settings.PUSHOVER_APP_TOKEN,
        "user": settings.PUSHOVER_ADMIN_USER,
        "message": message,
    }
    response = requests.post(
        "https://api.pushover.net:443/1/messages.json", timeout=7, data=data)
    return response
