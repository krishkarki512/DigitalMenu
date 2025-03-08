from django.contrib import admin
from .models import User, MenuItem, Order, OrderItem, Payment, Category

admin.site.register(User)
admin.site.register(MenuItem)
admin.site.register(Category)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)