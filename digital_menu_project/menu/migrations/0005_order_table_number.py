# Generated by Django 5.1.6 on 2025-03-04 19:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0004_remove_order_menu_items_alter_order_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='table_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
