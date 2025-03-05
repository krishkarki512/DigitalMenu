# menu/forms.py
from django import forms
from .models import MenuItem, Order
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number']

class UserProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']

class ModifyOrderForm(forms.Form):
    """Form for modifying an existing order."""
    
    def __init__(self, *args, **kwargs):
        super(ModifyOrderForm, self).__init__(*args, **kwargs)
        
        # Fetch all menu items dynamically
        self.menu_items = MenuItem.objects.all()
        
        for item in self.menu_items:
            self.fields[f'item_{item.id}'] = forms.IntegerField(
                label=f"{item.name} ($ {item.price})",
                min_value=0,
                required=False,
                initial=0
            )

    def clean(self):
        """Ensure that at least one item is ordered."""
        cleaned_data = super().clean()
        items = {}

        for item in self.menu_items:
            quantity = cleaned_data.get(f'item_{item.id}', 0)
            if quantity > 0:
                items[item.id] = quantity  # Store item ID and quantity

        if not items:
            raise forms.ValidationError("You must order at least one item.")

        # Store cleaned items for access in the view
        cleaned_data['items'] = items
        return cleaned_data

from django import forms
from .models import MenuItem

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'image_url', 'is_hot_deal']

class OrderForm(forms.ModelForm):
    table_number = forms.ChoiceField(choices=[(i, f"Table {i}") for i in range(1, 21)])  # Example: 20 tables

    class Meta:
        model = Order
        fields = ['table_number']
