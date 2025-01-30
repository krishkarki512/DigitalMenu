from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'home.html')

# View for Admin Dashboard
def admin_dashboard(request):
    return render(request, 'admin.html')

# View for Customer Menu
def customer_menu(request):
    return render(request, 'customer.html')

# View for Chef Orders
def chef_orders(request):
    return render(request, 'chef.html')