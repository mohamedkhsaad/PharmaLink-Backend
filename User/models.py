"""
The following models define the structure for user data and custom tokens used for user authentication.
"""

# Import necessary modules and classes
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
import secrets
from django.contrib.auth.models import AbstractUser, PermissionsMixin

# Custom user model representing a user of the application
class User(AbstractUser, PermissionsMixin):
    """
    Custom user model representing a user of the application.
    
    - Extends AbstractUser and PermissionsMixin to inherit authentication and permission-related fields and methods.
    - Defines fields for user data such as first name, last name, username, password, birthdate, email, phone, gender, chronic disease, etc.
    - Provides custom validation for the password field using a RegexValidator to enforce specific criteria (minimum length, lowercase, uppercase, digit, special character).
    - Includes choices for the gender field and chronic disease field.
    - Implements a clean() method to perform additional validation, ensuring the password meets the required criteria.
    - Overrides the __str__() method to provide a string representation of the user object (email).
    """
    id = models.AutoField(primary_key=True)
    fname = models.CharField(max_length=255)
    lname = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='user_images/', null=True, blank=True)
    
    # Custom password validation
    password_validator = RegexValidator(
        regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
        message="Password must contain at least one lowercase letter, one uppercase letter, one digit, and one special character."
    )
    password = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(limit_value=8), password_validator]
    )    
    
    birthdate = models.DateField()
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    
    # Choices for gender field
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices)
    chronic_disease = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def clean(self):
        """
        Custom clean method to perform additional validation.
        """
        super().clean()
        # Custom password validation
        if not self.password_validator(self.password):
            raise ValidationError("Password does not meet the required criteria.")
        
    def __str__(self):
        """
        String representation of the user object.
        """
        return self.email

# Custom token model representing tokens used for user authentication
class CustomToken(models.Model):
    """
    Custom token model representing tokens used for user authentication.
    
    - Defines fields for token key, associated user, email, and creation timestamp.
    - Ensures token key uniqueness and sets it as a random hex string if not provided.
    - Sets the associated email from the user object if not provided.
    - Overrides the save() method to handle token key generation and email assignment.
    - Provides verbose names for the model and its plural form for better readability in the admin interface.
    """
    key = models.CharField(max_length=64, unique=True, blank=True)
    user = models.ForeignKey(User, related_name='custom_tokens', on_delete=models.CASCADE)
    email = models.EmailField()
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
            self.email = self.user.email
        return super().save(*args, **kwargs)