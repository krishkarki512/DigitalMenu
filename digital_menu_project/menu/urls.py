from django.urls import path
from . import views
from . import admin_views
from . import payment_views
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

    path('admin_dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('add_menu_item/', admin_views.add_menu_item, name='add_menu_item'),
    path('edit_menu_item/<int:item_id>/', admin_views.edit_menu_item, name='edit_menu_item'),
    path('delete_menu_item/<int:item_id>/', admin_views.delete_menu_item, name='delete_menu_item'),
    path('update_order_status/<int:order_id>/', admin_views.update_order_status, name='update_order_status'),
    path('delete_order/<int:order_id>/', admin_views.delete_order, name='delete_order'),
    path('delete_user/<int:user_id>/', admin_views.delete_user, name='delete_user'),
    path('edit_user/<int:user_id>/', admin_views.edit_user, name='edit_user'),
    path('update_order/<int:order_id>/', admin_views.update_order, name='update_order'),

    path('profile/', views.profile, name='profile'),
    path('customer/', views.customer_menu, name='customer_menu'),
    path('add_to_cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/place_order/', views.place_order, name='place_order'),
    path('order_history/', views.order_history, name='order_history'),
    path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('order/modify/<int:order_id>/', views.modify_order, name='modify_order'),


    path('checkout/<int:order_id>/', payment_views.checkout, name='checkout'),
    path('khalti/initiate/', payment_views.initiate_khalti, name='initiate_khalti'),
    path('khalti/verify/', payment_views.verify_khalti, name='verify_khalti'),
]
