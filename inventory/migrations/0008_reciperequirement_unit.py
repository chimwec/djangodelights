# Generated by Django 5.0.3 on 2024-05-07 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_remove_reciperequirement_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='reciperequirement',
            name='unit',
            field=models.CharField(choices=[('g', 'gram'), ('tbsp', 'tablespoon'), ('tsp', 'teaspoon'), ('l', 'liter'), ('cup', 'cup'), ('oz', 'ounces'), ('lbs', 'pound'), ('', '')], default='', max_length=200),
        ),
    ]
