# Generated by Django 4.2b1 on 2024-02-21 00:14

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DrugEye',
            fields=[
                ('TradeName', models.CharField(max_length=255)),
                ('ID', models.IntegerField(primary_key=True, serialize=False)),
                ('ScName', models.CharField(max_length=255)),
                ('HOWMUCH', models.IntegerField()),
                ('Unit', models.CharField(max_length=100)),
                ('CLASSIFICATION', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('session_id', models.AutoField(primary_key=True, serialize=False)),
                ('doctor_id', models.IntegerField()),
                ('user_id', models.IntegerField()),
                ('otp', models.PositiveIntegerField()),
                ('verified', models.BooleanField(default=False)),
                ('ended', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('doctor_id', models.IntegerField()),
                ('user_id', models.IntegerField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('drugs', models.JSONField()),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescriptions', to='Prescription.session')),
            ],
        ),
        migrations.CreateModel(
            name='Drug',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('state', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('new', 'new')], max_length=100)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('quantity', models.IntegerField()),
                ('quantity_unit', models.CharField(max_length=100)),
                ('rate', models.IntegerField()),
                ('rate_unit', models.CharField(max_length=100)),
                ('DrugEye', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Prescription.drugeye')),
            ],
        ),
    ]
