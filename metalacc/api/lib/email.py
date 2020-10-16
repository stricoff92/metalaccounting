
from django.core.mail import send_mail

from api.utils import get_account_activation_url

def send_account_activation_email(user, token:str):
    activation_url = get_account_activation_url(user.userprofile.slug, token)

    from_email = None
    to_emails = [user.email]
    email_message = f"Your MetalAccounting profile is ready. Click to activate your account: {activation_url}"
    send_mail(
        'Activate Your Account',
        email_message,
        from_email,
        to_emails,
        fail_silently=False,
    )
