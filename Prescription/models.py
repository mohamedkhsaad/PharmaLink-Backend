from django.db import models

# Create your models here.
from djongo import models

class Drug(models.Model):
    drug_id = models.IntegerField()
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
    drugs = models.ManyToManyField(Drug)
    doctor_id = models.IntegerField()
    user_id = models.IntegerField()

class DrugEye(models.Model):
    TradeName = models.CharField(max_length=255)
    ID = models.IntegerField(primary_key=True)  # Assuming this is the primary key
    ScName = models.CharField(max_length=255)
    HOWMUCH = models.IntegerField()
    Unit = models.CharField(max_length=100)
    CLASSIFICATION = models.CharField(max_length=100)
    def __str__(self):
        return self.trade_name
    

class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    doctor_id = models.IntegerField()
    user_id = models.IntegerField()
    otp = models.PositiveIntegerField() 
    verified = models.BooleanField(default=False)
    ended = models.BooleanField(default=False) 
