# Generated by Django 5.0.3 on 2024-05-25 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0010_reciperequirement_price_per_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reciperequirement',
            name='price_per_unit',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10),
        ),
    ]
