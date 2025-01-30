from django.urls import path
from . import views
from . import auth_views as custom_auth_views

urlpatterns = [
    path('', views.index, name='index'),  # index.html
    path('login_register/', custom_auth_views.login_register_view, name='login_register'),
    path('logout/', custom_auth_views.logout_view, name='logout'),
    path('confirm_email/', custom_auth_views.confirm_email, name='confirm_email'),
    path('forgot_password/', custom_auth_views.forgot_password, name='forgot_password'),
    path('verify_otp/', custom_auth_views.verify_otp, name='verify_otp'),
    path('reset_password/', custom_auth_views.reset_password, name='reset_password'),
    path('resend_otp/', custom_auth_views.resend_otp, name='resend_otp'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('customer/', views.customer_menu, name='customer_menu'),
    path('chef/', views.chef_orders, name='chef_orders'),
]
