import random
import re
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from decimal import Decimal
from datetime import datetime
from django.utils import timezone

def generate_otp():
    """
    Generate a random six-digit OTP (One-Time Password).
    """
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp_email(user, subject, purpose):
    """
    Send an OTP email to the user.
    """
    context = {
        'user': user,
        'otp': user.otp,
        'purpose': purpose
    }
    html_message = render_to_string('email/otp_email.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email

    msg = EmailMultiAlternatives(subject, plain_message, from_email, [to_email])
    msg.attach_alternative(html_message, "text/html")
    msg.send()

def is_password_valid(password):
    """
    Validate the password to ensure it meets the required criteria:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""
