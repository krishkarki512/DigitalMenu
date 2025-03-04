from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import MenuItem, Order, OrderItem
from .forms import MenuItemForm
from django.contrib import messages
from django.db.models import Sum, Count

User = get_user_model()

# Check if the user is an admin
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Fetching data
    menu_items = MenuItem.objects.all()
    orders = Order.objects.all()
    users = User.objects.all()

    # Statistics
    total_orders = orders.count()
    total_revenue = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_users = users.count()
    
    # Get top-selling items
    top_items = (
        OrderItem.objects.values('menu_item__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )

    return render(request, 'admin_dashboard.html', {
        'menu_items': menu_items,
        'orders': orders,
        'users': users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_users': total_users,
        'top_items': top_items,
    })

@login_required
@user_passes_test(is_admin)
def add_menu_item(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')  # Redirect to the admin dashboard after saving
    else:
        form = MenuItemForm()

    return render(request, 'add_menu_item.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def edit_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')  # Redirect to the admin dashboard after saving
    else:
        form = MenuItemForm(instance=item)

    return render(request, 'edit_menu_item.html', {'form': form, 'item': item})

@login_required
@user_passes_test(is_admin)
def delete_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item.delete()
    return redirect('admin_dashboard')  # Redirect back to the admin dashboard after deletion

@login_required
@user_passes_test(is_admin)
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        return redirect('admin_dashboard')  # Redirect to the admin dashboard after updating status

    return render(request, 'update_order_status.html', {'order': order})

@login_required
@user_passes_test(is_admin)
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()

    return redirect('admin_dashboard')

from .forms import UserUpdateForm  # Create this form in step 3

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully!")
            return redirect('admin_dashboard')
    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'edit_user.html', {'form': form, 'user': user})

def update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        table_number = request.POST.get("table_number")
        if table_number:
            order.table_number = table_number
            order.save()
    
    return redirect("admin_dashboard")
