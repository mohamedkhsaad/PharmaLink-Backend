from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
import secrets
from django.contrib.auth.models import AbstractUser, PermissionsMixin

class User(AbstractUser, PermissionsMixin):
    """
    Custom user model representing a user of the application.
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
    
    # Choices for chronic disease field
    CHRONIC_DISEASE_CHOICES = [
        ('ALS', "ALS (Lou Gehrig's Disease)"),
        ('Alzheimer', "Alzheimer's Disease and other Dementias"),
        # Add more choices as needed
    ]
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

class CustomToken(models.Model):
    """
    Custom token model representing tokens used for user authentication.
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