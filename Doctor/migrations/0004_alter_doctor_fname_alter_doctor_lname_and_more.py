# Generated by Django 4.2b1 on 2024-04-01 18:00

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Doctor', '0003_doctor_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctor',
            name='fname',
            field=models.CharField(max_length=255, validators=[django.core.validators.RegexValidator(code='invalid_fname', message='First name must contain only letters.', regex='^[A-Za-z]+$')]),
        ),
        migrations.AlterField(
            model_name='doctor',
            name='lname',
            field=models.CharField(max_length=255, validators=[django.core.validators.RegexValidator(code='invalid_lname', message='Last name must contain only letters.', regex='^[A-Za-z]+$')]),
        ),
        migrations.AlterField(
            model_name='doctor',
            name='username',
            field=models.CharField(max_length=255, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_username', message='Username must contain only letters, numbers, and underscores.', regex='^[a-zA-Z0-9_]+$')]),
        ),
    ]