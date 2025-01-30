from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import IntegrityError
from django.utils import timezone

from .utils import generate_otp, send_otp_email, is_password_valid

User = get_user_model()

def login_register_view(request):
    form_mode = 'signin'  # Default mode

    if request.method == "POST":
        if 'signin' in request.POST:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.email_confirmed:
                    login(request, user)
                    if user.is_superuser:
                        return redirect('admin_dashboard')
                    else:
                        return redirect('customer_menu')
                else:
                    messages.error(request, "Please confirm your email before logging in.")
                    request.session['user_id'] = user.id
                    return redirect('confirm_email')
            else:
                messages.error(request, "Invalid username and/or password.", extra_tags='signin')
                return render(request, 'login_register.html', {'form_mode': 'signin'})

        elif 'signup' in request.POST:
            username = request.POST["username"]
            email = request.POST["email"]
            password = request.POST["password"]
            confirmation = request.POST["confirmation"]

            if password != confirmation:
                messages.error(request, "Passwords must match.", extra_tags='signup')
                return render(request, 'login_register.html', {'form_mode': 'signup'})

            is_valid, validation_message = is_password_valid(password)
            if not is_valid:
                messages.error(request, validation_message, extra_tags='signup')
                return render(request, 'login_register.html', {'form_mode': 'signup'})

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already in use.", extra_tags='signup')
                return render(request, 'login_register.html', {'form_mode': 'signup'})

            try:
                user = User.objects.create_user(username, email, password)
                user.email_confirmed = False
                user.otp = generate_otp()
                user.otp_expiration = timezone.now() + timezone.timedelta(minutes=10)
                user.save()
                send_otp_email(user, 'Your OTP Code', 'confirm your email')
                messages.success(request, "Check your email for the OTP code to confirm your email.")
                request.session['user_id'] = user.id
                return redirect('confirm_email')
            except IntegrityError:
                messages.error(request, "Username already taken.", extra_tags='signup')
                return render(request, 'login_register.html', {'form_mode': 'signup'})

    return render(request, "login_register.html", {'form_mode': form_mode})

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def confirm_email(request):
    if request.method == 'POST':
        otp = request.POST['otp']
        try:
            user = User.objects.get(otp=otp)
            if user.email_confirmed:
                messages.info(request, "Email already confirmed.")
                return redirect('login_register')

            if timezone.now() > user.otp_expiration:
                messages.error(request, "OTP has expired.")
                user.otp = generate_otp()  # Regenerate OTP
                user.otp_expiration = timezone.now() + timezone.timedelta(minutes=10)
                user.save()
                send_otp_email(user, 'Your OTP Code', 'confirm your email')
                messages.info(request, "A new OTP has been sent to your email.")
                request.session['user_id'] = user.id
                return redirect('confirm_email')

            user.email_confirmed = True
            user.otp = None
            user.otp_expiration = None
            user.save()
            messages.success(request, "Email confirmed successfully. Please log in.")
            return redirect('login_register')
        except User.DoesNotExist:
            messages.error(request, "Invalid OTP.")
            return redirect('confirm_email')
    return render(request, 'confirm_email.html')

def forgot_password(request):
    if request.method == "POST":
        email = request.POST["email"]
        try:
            user = User.objects.get(email=email)
            user.otp = generate_otp()  # Generate OTP
            user.otp_expiration = timezone.now() + timezone.timedelta(minutes=10)
            user.save()
            send_otp_email(user, 'Password Reset OTP', 'reset your password')
            messages.success(request, "Check your email for the OTP code to reset your password.")
            request.session['user_id'] = user.id
            return redirect('verify_otp')
        except User.DoesNotExist:
            messages.error(request, "Email not found.")
            return redirect('forgot_password')
    return render(request, "forgot_password.html")

def verify_otp(request):
    if request.method == "POST":
        otp = request.POST['otp']
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Session expired. Please try again.")
            return redirect('forgot_password')
        
        try:
            user = User.objects.get(id=user_id, otp=otp)
            if timezone.now() > user.otp_expiration:
                messages.error(request, "OTP has expired.")
                user.otp = generate_otp()  # Regenerate OTP
                user.otp_expiration = timezone.now() + timezone.timedelta(minutes=10)
                user.save()
                send_otp_email(user, 'Password Reset OTP', 'reset your password')
                messages.info(request, "A new OTP has been sent to your email.")
                return redirect('verify_otp')
            
            request.session['otp_verified'] = True
            return redirect('reset_password')
        except User.DoesNotExist:
            messages.error(request, "Invalid OTP.")
            return redirect('verify_otp')
    return render(request, "verify_otp.html")

def reset_password(request):
    if not request.session.get('otp_verified'):
        messages.error(request, "OTP verification required.")
        return redirect('forgot_password')

    if request.method == "POST":
        new_password = request.POST['new_password']
        confirmation = request.POST['confirmation']
        
        if new_password != confirmation:
            messages.error(request, "Passwords must match.")
            return redirect('reset_password')

        # Validate the new password
        is_valid, validation_message = is_password_valid(new_password)
        if not is_valid:
            messages.error(request, validation_message)
            return redirect('reset_password')

        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, "Session expired. Please try again.")
            return redirect('forgot_password')

        try:
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.otp = None
            user.otp_expiration = None
            user.save()
            messages.success(request, "Password reset successfully. Please log in.")
            return redirect('login_register')
        except User.DoesNotExist:
            messages.error(request, "An error occurred. Please try again.")
            return redirect('reset_password')
    return render(request, "reset_password.html")
    
def resend_otp(request):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        
        if not user_id:
            messages.error(request, "Session expired. Please try again.")
            return redirect('login_register')
        
        try:
            user = User.objects.get(id=user_id)
            user.otp = generate_otp()
            user.otp_expiration = timezone.now() + timezone.timedelta(minutes=10)
            user.save()
            
            send_otp_email(user, 'Verify Your OTP', 'verify your action')
            
            messages.info(request, "A new OTP has been sent to your email.")
            
            if 'verify_otp' in request.META.get('HTTP_REFERER', ''):
                return redirect('verify_otp')
            else:
                return redirect('confirm_email')
        
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('forgot_password')
    
    return render(request, "verify_otp.html")