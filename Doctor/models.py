"""
The following models represent Doctor-related information and custom authentication tokens.
"""

# Import necessary modules and classes
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinLengthValidator
from django.db import models
from django.core.exceptions import ValidationError
import secrets

# Model for Doctor information
class Doctor(AbstractUser):
    """
    Model representing Doctor information.

    - Inherits from Django's AbstractUser, providing basic user functionality.
    - Defines additional fields specific to Doctor profiles such as first name, last name, gender, etc.
    - Specifies custom validation for the password field to ensure complexity requirements.
    - Includes image field for profile pictures.
    - Defines permissions for viewing users.
    """
    id = models.AutoField(primary_key=True)
    fname = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z]+$',
                message='First name must contain only letters.',
                code='invalid_fname'
            )
        ]
    )
    lname = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z]+$',
                message='Last name must contain only letters.',
                code='invalid_lname'
            )
        ]
    )
     # Username with custom regex validation
    username = models.CharField(
        max_length=255,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]+$',
                message='Username must contain only letters, numbers, and underscores.',
                code='invalid_username'
            )
        ]
    )
    gender_choices = [
        ("M", "Male"),
        ("F", "Female")
    ]
    gender = models.CharField(max_length=1, choices=gender_choices)
    email = models.EmailField(unique=True)
    birthdate = models.DateField()
    phone = models.CharField(max_length=20)
    license_number = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    graduation_date = models.DateField()
    university = models.CharField(max_length=255)
    password_validator = RegexValidator(
        regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
        message="Password must contain at least one lowercase letter, one uppercase letter, one digit, and one special character."
    )
    password = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(limit_value=8), password_validator]
    )
    image = models.ImageField(upload_to='doctor_images/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def clean(self):
        """
        Custom validation method for Doctor instances.

        - Overrides the clean method to include additional validation for the password field.
        """

        super().clean()
        # Custom password validation
        if not self.password_validator(self.password):
            raise ValidationError("Password does not meet the required criteria.")

    def __str__(self):
        """
        Method to represent Doctor objects as strings.
        """
        return self.email
    class Meta:
        """
        Meta class for Doctor model.
        """
        permissions = [("view_user", "Can view user")]

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        related_name="doctor_set",
        related_query_name="doctor",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        related_name="doctor_set",
        related_query_name="doctor",
    )

# Model for custom authentication tokens
class CustomToken(models.Model):
    """
    Custom token model representing tokens used for doctor authentication.
    
    - Defines fields for token key, associated doctor, email, access token, refresh token,
      and creation timestamp.
    - Ensures token key uniqueness and sets it as a random hex string if not provided.
    - Sets the associated email from the doctor object if not provided.
    - Overrides the save() method to handle token key generation and email assignment.
    - Provides verbose names for the model and its plural form for better readability in the admin interface.
    """
    key = models.CharField(max_length=64, unique=True, blank=True)
    doctor = models.ForeignKey(Doctor, related_name='custom_tokens', on_delete=models.CASCADE)
    email = models.EmailField()
    access_token = models.CharField(max_length=255, blank=True)
    refresh_token = models.CharField(max_length=255, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'CustomToken'
        verbose_name_plural = 'CustomTokens'

    def save(self, *args, **kwargs):
        """
        Custom save method to generate token key and set email if not provided.
        """
        if not self.key:
            # Generate a random token key
            self.key = secrets.token_hex(32)
        if not self.email:
            # Set email from associated user if not provided
            self.email = self.doctor.email
        return super().save(*args, **kwargs)