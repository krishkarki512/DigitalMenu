from django.shortcuts import render
from .models import MenuItem

def index(request):
    return render(request, 'index.html')

# View for Admin Dashboard
def admin_dashboard(request):
    return render(request, 'admin.html')

# View for Customer Menu
def customer_menu(request):
    menu_items = MenuItem.objects.all()
    return render(request, 'customer.html', {'menu_items': menu_items})

# View for Chef Orders
def chef_orders(request):
    return render(request, 'chef.html')