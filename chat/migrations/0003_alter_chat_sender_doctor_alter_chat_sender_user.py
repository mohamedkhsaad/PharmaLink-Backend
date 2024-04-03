# Generated by Django 4.2b1 on 2024-04-02 23:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Doctor', '0004_alter_doctor_fname_alter_doctor_lname_and_more'),
        ('chat', '0002_alter_chat_receiver_doctor_alter_chat_receiver_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='sender_doctor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to='Doctor.doctor'),
        ),
        migrations.AlterField(
            model_name='chat',
            name='sender_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL),
        ),
    ]