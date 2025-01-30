from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # index.html
    path('home/', views.home, name='home'),  # home.html
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('customer/', views.customer_menu, name='customer_menu'),
    path('chef/', views.chef_orders, name='chef_orders'),
]
