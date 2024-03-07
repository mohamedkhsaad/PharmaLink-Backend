# Import necessary modules
from django.db import models
from django.utils import timezone

# Django model to represent drug information
class DrugEye(models.Model):
    """
    Django model to represent drug information obtained from DrugEye.

    - Inherits from the Django's `models.Model` class.
    - Represents a table in the database to store drug information.
    """

    # Primary key field for the model
    id = models.AutoField(primary_key=True)

    # Fields to store drug details
    TradeName = models.CharField(max_length=255)
    ID = models.CharField(max_length=255)
    ScName = models.CharField(max_length=255)
    HOWMUCH = models.IntegerField()
    Unit = models.CharField(max_length=100)
    CLASSIFICATION = models.CharField(max_length=100)

    def __str__(self):
        """
        Returns a string representation of the model instance.

        Returns:
            - str: A string representation of the DrugEye instance.
        """
        return self.TradeName


# Django model to represent user sessions
class Session(models.Model):
    """
    Django model to represent user sessions.

    - Inherits from the Django's `models.Model` class.
    - Represents a table in the database to store session information.
    """

    # Primary key field for the model
    session_id = models.AutoField(primary_key=True)

    # Fields to store session details
    doctor_id = models.IntegerField()
    user_id = models.IntegerField()
    otp = models.PositiveIntegerField()
    verified = models.BooleanField(default=False)
    ended = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)


# Django model to represent drugs prescribed to users
class Drug(models.Model):
    """
    Django model to represent drugs prescribed to users.

    - Inherits from the Django's `models.Model` class.
    - Represents a table in the database to store drug prescription details.
    """

    # Primary key field for the model
    id = models.AutoField(primary_key=True)

    # Foreign key field to relate to DrugEye model
    DrugEye = models.ForeignKey('DrugEye', on_delete=models.CASCADE)

    # Choices for drug state
    STATE_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('new', 'New'),
    ]

    # Fields to store drug prescription details
    state = models.CharField(max_length=100, choices=STATE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    quantity = models.IntegerField()
    quantity_unit = models.CharField(max_length=100)
    rate = models.IntegerField()
    rate_unit = models.CharField(max_length=100)


# Django model to represent prescriptions
class Prescription(models.Model):
    """
    Django model to represent prescriptions.

    - Inherits from the Django's `models.Model` class.
    - Represents a table in the database to store prescription details.
    """

    # Primary key field for the model
    id = models.AutoField(primary_key=True)

    # Foreign key field to relate to Session model
    session = models.ForeignKey(Session, related_name='prescriptions', on_delete=models.CASCADE)

    # Fields to store prescription details
    doctor_id = models.IntegerField()
    user_id = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    drugs = models.JSONField()  # Assuming drugs are stored as JSON data

    def __str__(self):
        """
        Returns a string representation of the model instance.

        Returns:
            - str: A string representation of the Prescription instance.
        """
        return f"Prescription {self.id} for User {self.user_id} by Doctor {self.doctor_id}"
