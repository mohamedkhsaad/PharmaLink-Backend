# Generated by Django 4.2b1 on 2024-04-03 07:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Doctor', '0004_alter_doctor_fname_alter_doctor_lname_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customtoken',
            name='access_token',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='customtoken',
            name='refresh_token',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
