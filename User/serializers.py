from rest_framework import serializers
from .models import User
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """
    class Meta:
        model = User
        # Define fields to be serialized
        fields = ['id', 'fname', 'lname', 'username', 'password', 'birthdate', 'email', 'phone', 'gender', 'chronic_disease', 'image']
        # Specify extra kwargs for fields
        extra_kwargs = {'password': {'write_only': True}}

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    # Field for username or email (maximum length: 255 characters)
    username_or_email = serializers.CharField(max_length=255)
    # Field for password (write-only)
    password = serializers.CharField(write_only=True)
    
class AuthTokenSerializer(serializers.Serializer):
    """
    Serializer for user authentication token.
    """
    # Field for email (must be a valid email)
    email = serializers.EmailField()
    # Field for password (with style for input type password, trim_whitespace set to False)
    password = serializers.CharField(style={'input_type': 'password'},
                                     trim_whitespace=False)

class PasswordResetRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for password reset request.
    """
    class Meta:
        model = User
        # Define fields to be serialized
        fields = ['email']

class PasswordUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating user password.
    """
    # Field for new password (write-only, required)
    password = serializers.CharField(write_only=True, required=True)

    def update(self, instance, validated_data):
        """
        Updates the user's password.
        """
        # Set the new password
        instance.set_password(validated_data['password'])
        # Save the instance
        instance.save()
        return instance