
from django.db import models
from django.utils import timezone

class DrugEye(models.Model):
    TradeName = models.CharField(max_length=255)
    ID = models.IntegerField(primary_key=True) 
    ScName = models.CharField(max_length=255)
    HOWMUCH = models.IntegerField()
    Unit = models.CharField(max_length=100)
    CLASSIFICATION = models.CharField(max_length=100)
    def __str__(self):
        return self.TradeName

class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    doctor_id = models.IntegerField()
    user_id = models.IntegerField()
    otp = models.PositiveIntegerField() 
    verified = models.BooleanField(default=False)
    ended = models.BooleanField(default=False) 
    created_at = models.DateTimeField(default=timezone.now) 

class Drug(models.Model):
    id = models.AutoField(primary_key=True)
    DrugEye = models.ForeignKey('DrugEye', on_delete=models.CASCADE)
    STATE_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('new', 'new'),
    ]
    state = models.CharField(max_length=100, choices=STATE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    quantity = models.IntegerField()
    quantity_unit = models.CharField(max_length=100)
    rate = models.IntegerField()
    rate_unit = models.CharField(max_length=100)
    

class Prescription(models.Model):
    id = models.AutoField(primary_key=True)
    session = models.ForeignKey(Session, related_name='prescriptions', on_delete=models.CASCADE)
    doctor_id = models.IntegerField()
    user_id = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    drugs = models.JSONField()  # Assuming drugs are stored as JSON data

    def __str__(self):
        return f"Prescription {self.id} for User {self.user_id} by Doctor {self.doctor_id}"

