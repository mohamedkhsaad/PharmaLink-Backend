from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, RegexValidator
import secrets
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.
class User(models.Model):
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



    # def save(self, *args, **kwargs):
    #     if not self.id:  # Only hash the password for new instances
    #         self.password = make_password(self.password)
    #     super().save(*args, **kwargs)
   
    def clean(self):
        super().clean()
        # Custom password validation
        if not self.password_validator(self.password):
            raise ValidationError("Password does not meet the required criteria.")
        
    def __str__(self):
        return self.email
    
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