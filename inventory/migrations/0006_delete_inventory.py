# Generated by Django 5.0.3 on 2024-04-11 05:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_rename_available_quantity_ingredient_quantity_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Inventory',
        ),
    ]