from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.contrib.auth.decorators import login_required
from .models import MenuItem, Order, OrderItem
from .forms import UserProfileForm, ModifyOrderForm
from django.contrib import messages
from .forms import ModifyOrderForm

def index(request):
    return render(request, 'index.html')

def customer_menu(request):
    query = request.GET.get('q', '')
    
    # Initially, fetch all menu items
    menu_items = MenuItem.objects.all()

    # If there is a search query, filter the menu items
    if query:
        menu_items = menu_items.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Implement pagination after the filtering
    paginator = Paginator(menu_items, 6)  # Show 6 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # AI-Based Recommendations: Only generate recommendations if there is a search query
    recommended_items = []
    if query:
        all_items = list(MenuItem.objects.all())
        item_texts = [item.description for item in all_items]

        if item_texts:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(item_texts)
            cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

            item_indices = {item.id: idx for idx, item in enumerate(all_items)}
            recommended_items_set = set()

            for item in menu_items:
                idx = item_indices.get(item.id)
                if idx is not None:
                    similar_scores = list(enumerate(cosine_sim[idx]))
                    similar_scores = sorted(similar_scores, key=lambda x: x[1], reverse=True)[1:4]

                    for i, _ in similar_scores:
                        recommended_items_set.add(all_items[i])

            recommended_items = list(recommended_items_set)

    hot_deals = MenuItem.objects.filter(is_hot_deal=True)

    return render(request, 'customer.html', {
        'page_obj': page_obj,
        'query': query,
        'recommended_items': recommended_items,
        'hot_deals': hot_deals
    })


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'profile.html', {'form': form})

def add_to_cart(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)
    cart = request.session.get('cart', {})

    if str(item_id) in cart:
        cart[str(item_id)] += 1
    else:
        cart[str(item_id)] = 1

    request.session['cart'] = cart
    return redirect('customer_menu')

def view_cart(request):
    # Get the cart from the session
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for item_id, quantity in cart.items():
        menu_item = MenuItem.objects.get(id=item_id)
        item_total = menu_item.price * quantity
        total_price += item_total
        cart_items.append({'item': menu_item, 'quantity': quantity, 'item_total': item_total})

    # Get the list of tables that are currently occupied (those with pending or confirmed orders)
    occupied_tables = Order.objects.filter(status__in=["Pending", "Confirmed"]).values_list('table_number', flat=True)
    
    # Get available tables (1-20, except occupied ones)
    tables = [i for i in range(1, 21) if i not in occupied_tables]

    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price, 'tables': tables})

def remove_from_cart(request, item_id):
    # Convert item_id to string (because it is stored as a string in the cart)
    item_id_str = str(item_id)
    
    # Get the cart from the session
    cart = request.session.get('cart', {})
    
    # Remove the item from the cart if it exists
    if item_id_str in cart:
        del cart[item_id_str]
    
    # Save the updated cart back to the session
    request.session['cart'] = cart
    
    # Redirect back to the cart page
    return redirect('view_cart')

def place_order(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('customer_menu')  # Redirect if cart is empty

    if request.method == "POST":
        table_number = request.POST.get('table_number')  # Get selected table number
        if not table_number:
            return render(request, 'cart.html', {'error': 'Please select a table!'})  # Show error if no table selected

        # Check if the table is already occupied
        if Order.objects.filter(table_number=table_number, status="Pending").exists():
            messages.error(request, f"Table {table_number} is already occupied. Please choose another table.")
            return redirect('cart')  # Redirect back to cart page to select another table

        cart_items = []
        total_price = 0

        for item_id, quantity in cart.items():
            menu_item = MenuItem.objects.get(id=item_id)
            item_total = menu_item.price * quantity
            total_price += item_total
            cart_items.append({'item': menu_item, 'quantity': quantity, 'item_total': item_total})

        # Create the order with selected table number
        order = Order.objects.create(
            user=request.user,
            table_number=table_number,  # Store table number
            total_price=total_price
        )

        # Create OrderItems for each cart item
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=item['item'],
                quantity=item['quantity']
            )

        # Clear the cart after order placement
        request.session['cart'] = {}

        return render(request, 'order_confirmation.html', {'order': order, 'cart_items': cart_items})

    return redirect('cart')

@login_required
def order_history(request):
    """Displays a list of past orders for the logged-in user."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Get details of each order and associated items
    order_details = []
    for order in orders:
        items = OrderItem.objects.filter(order=order)
        order_details.append({
            'order': order,
            'items': items
        })

    return render(request, 'order_history.html', {'order_details': order_details})

@login_required
def cancel_order(request, order_id):
    """Allows users to cancel an order if it's still pending."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status == 'Pending':  # Only cancel if order is still pending
        order.status = 'Cancelled'
        order.save()
        messages.success(request, "Your order has been cancelled.")
    else:
        messages.error(request, "You cannot cancel this order.")

    return redirect('order_history')

@login_required
def modify_order(request, order_id):
    """Allows users to modify their order if it's still pending."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != 'Pending':  # Only modify if the order is pending
        messages.error(request, "You can only modify pending orders.")
        return redirect('order_history')

    if request.method == 'POST':
        form = ModifyOrderForm(request.POST)
        if form.is_valid():
            items = form.cleaned_data['items']  # ✅ This prevents KeyError

            # Remove old order items
            order.orderitem_set.all().delete()

            # Create new order items
            total_price = 0
            for menu_item_id, quantity in items.items():
                menu_item = MenuItem.objects.get(id=menu_item_id)
                OrderItem.objects.create(order=order, menu_item=menu_item, quantity=quantity)
                total_price += menu_item.price * quantity

            # Update order total price
            order.total_price = total_price
            order.save()

            messages.success(request, "Your order has been updated.")
            return redirect('order_history')
    else:
        # Prepopulate form with existing order data
        initial_data = {f'item_{item.menu_item.id}': item.quantity for item in order.orderitem_set.all()}
        form = ModifyOrderForm(initial=initial_data)

    return render(request, 'modify_order.html', {'form': form, 'order': order})