from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
import secrets
from django.contrib.auth.models import AbstractUser, PermissionsMixin

class User(AbstractUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    fname = models.CharField(max_length=255)
    lname = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='user_images/', null=True, blank=True)
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
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices)
    CHRONIC_DISEASE_CHOICES = [
        ('ALS', "ALS (Lou Gehrig's Disease)"),
        ('Alzheimer', "Alzheimer's Disease and other Dementias"),
        ('Arthritis', 'Arthritis'),
        ('Asthma', 'Asthma'),
        ('Cancer', 'Cancer'),
        ('COPD', 'Chronic Obstructive Pulmonary Disease (COPD)'),
        ('Crohns', 'Crohn\'s Disease, Ulcerative Colitis, Other Inflammatory Bowel Diseases, Irritable Bowel Syndrome'),
        ('CysticFibrosis', 'Cystic Fibrosis'),
        ('Diabetes', 'Diabetes'),
        ('EatingDisorders', 'Eating Disorders'),
        ('HeartDisease', 'Heart Disease'),
        ('Obesity', 'Obesity'),
        ('OralHealth', 'Oral Health'),
        ('Osteoporosis', 'Osteoporosis'),
        ('RSD', 'Reflex Sympathetic Dystrophy (RSD) Syndrome'),
        ('SCA', 'Sudden Cardiac Arrest (SCA) in Youth'),
        ('TobaccoUse', 'Tobacco Use and Related Conditions'),
    ]
    chronic_disease = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        # Custom password validation
        if not self.password_validator(self.password):
            raise ValidationError("Password does not meet the required criteria.")
        
    def __str__(self):
        return self.email

# def add_image_fields(count):
#     """
#     This function generate auto image fields and resize the all images with a fix size
#     """
#     # Add first image field as 'image'
#     User.add_to_class('image', ResizedImageField(size=[512, 256],  crop=['middle', 'center'],
#                                                   upload_to='events/', blank=True, null=True, verbose_name='image'))
#     # Add remaining image fields with field names 'image2', 'image3', ...
#     for i in range(1, count+1):
#         field_name = f"image{i}"
#         field = ResizedImageField(size=[512, 256], crop=[
#                                   'middle', 'center'], upload_to='events/', blank=True, null=True, verbose_name=field_name)
#         User.add_to_class(field_name, field)
    
class CustomToken(models.Model):
    key = models.CharField(max_length=64, unique=True, blank=True)
    user = models.ForeignKey(User, related_name='custom_tokens', on_delete=models.CASCADE)
    email = models.EmailField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'CustomToken'
        verbose_name_plural = 'CustomTokens'

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(32)
        if not self.email:
            self.email = self.user.email
        return super().save(*args, **kwargs)