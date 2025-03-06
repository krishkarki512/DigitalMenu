from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.utils.http import urlencode
from django.conf import settings
import requests
import uuid
from decimal import Decimal
from .models import MenuItem, Order, Payment, OrderItem
from .utils import update_database_after_payment

@login_required
def checkout(request, order_id):
    # Fetch the order using the order_id
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Calculate total price from Order (already stored)
    total_price = order.total_price
    order_items = OrderItem.objects.filter(order=order)  # Get all items in the order

    if request.method == 'POST':
        request.session['order_id'] = order_id
        request.session['total_price'] = str(total_price)
        request.session['paymentMethod'] = request.POST['paymentMethod']

        # 🔥 Store the first item from the order in the session (for Khalti verification)
        first_order_item = order_items.first()
        if first_order_item:
            request.session['item_id'] = first_order_item.menu_item.id
            request.session['quantity'] = first_order_item.quantity

        if request.session['paymentMethod'] == 'khalti':
            base_url = reverse('initiate_khalti')
            query_params = urlencode({
                'return_url': request.build_absolute_uri(reverse('verify_khalti')),
                'amount': int(total_price * 100),  # Khalti requires amount in paisa
                'purchase_order_id': str(uuid.uuid4())
            })
            full_url = f"{base_url}?{query_params}"
            return redirect(full_url)

    context = {
        'order': order,
        'order_items': order_items,
        'total_price': total_price
    }
    return render(request, 'checkout.html', context)

def initiate_khalti(request):
    if request.method == 'GET':
        url = "https://a.khalti.com/api/v2/epayment/initiate/"
        return_url = request.GET.get('return_url')
        amount = request.GET.get('amount')
        purchase_order_id = request.GET.get('purchase_order_id')

        if not all([return_url, amount, purchase_order_id]):
            return HttpResponseBadRequest("Missing required parameters")

        payload = {
            "return_url": return_url,
            "website_url": "http://127.0.0.1:8000",
            "amount": amount,
            "purchase_order_id": purchase_order_id,
            "purchase_order_name": "Food Order",
            "customer_info": {
                "name": request.user.username,
                "email": request.user.email,
                "phone": 9821190537
            }
        }

        headers = {
            'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            if response.status_code == 200 and 'payment_url' in response_data:
                return redirect(response_data['payment_url'])
            else:
                return JsonResponse(response_data, status=response.status_code)
        except requests.RequestException as e:
            return JsonResponse({'error': str(e)}, status=500)


def verify_khalti(request):
    if request.method == 'GET':
        url = "https://a.khalti.com/api/v2/epayment/lookup/"
        pidx = request.GET.get('pidx')

        if not pidx:
            return HttpResponseBadRequest("Missing required parameters")

        headers = {
            'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
            'Content-Type': 'application/json',
        }

        payload = {'pidx': pidx}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status') == 'Completed':
                transaction_id = response_data.get('transaction_id')
                user = request.user
                amount = response_data['total_amount'] / 100  # Convert to correct amount
                order_id = request.session.get('order_id')
                order = get_object_or_404(Order, id=order_id, user=user)

                # Ensure item_id and quantity are in session
                item_id = request.session.get('item_id')
                if not item_id:
                    return HttpResponseBadRequest("Item ID is missing from the session")

                try:
                    menu_item = MenuItem.objects.get(id=item_id)
                except MenuItem.DoesNotExist:
                    return HttpResponseBadRequest("Invalid item ID. Menu item does not exist.")

                quantity = request.session.get('quantity')
                if not quantity:
                    return HttpResponseBadRequest("Quantity is missing from the session")

                # Save the payment details
                payment_details = Payment(
                    order=order,
                    transaction_id=transaction_id,
                    amount=amount,
                    payment_method='Khalti',
                    status='Completed'
                )
                payment_details.save()

                # Update the database (now just passing the order ID)
                update_database_after_payment(transaction_id, user, amount, 'Khalti', order.id)

                # Clear session data to prevent reuse
                del request.session['item_id']
                del request.session['quantity']
                del request.session['total_price']

                # Return success response
                context = {
                    'user': user,
                    'order': order,
                    'quantity': quantity,
                    'total_price': amount,
                    'transaction_id': transaction_id
                }
                return render(request, 'payment_success.html', context)

            else:
                return JsonResponse(response_data, status=response.status_code)

        except requests.RequestException as e:
            return JsonResponse({'error': str(e)}, status=500)

    return HttpResponseBadRequest("Invalid request method")