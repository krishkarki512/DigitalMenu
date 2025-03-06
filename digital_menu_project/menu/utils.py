import random
import re
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from decimal import Decimal
from datetime import datetime
from django.utils import timezone

from .models import Order, OrderItem, Payment
from decimal import Decimal

def update_database_after_payment(transaction_id, user, total_price, payment_method, order_id):
    try:
        # Retrieve the order using the order_id
        order = Order.objects.get(id=order_id, user=user)
        
        # Update the order payment status to 'Paid' and its status to 'Confirmed'
        order.payment_status = 'Paid'
        order.status = 'Confirmed'  # You can set this as per your business logic
        order.save()

        # Check if a payment already exists for this order
        payment = Payment.objects.filter(order=order).first()
        
        if payment:
            # If payment already exists, update the existing payment details
            payment.transaction_id = transaction_id
            payment.amount = Decimal(total_price)
            payment.payment_method = payment_method
            payment.status = 'Paid'
            payment.save()  # Save the updated payment
        else:
            # If no payment exists, create a new payment record
            payment = Payment(
                order=order,
                transaction_id=transaction_id,
                payment_method=payment_method,
                amount=Decimal(total_price),
                status='Paid'
            )
            payment.save()

        # You can also add any additional logic for updating order-related information

        return True  # Successfully updated or created the payment

    except Order.DoesNotExist:
        return False  # Return False if the order is not found
    except IntegrityError as e:
        return False  # Return False in case of integrity errors
    
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
