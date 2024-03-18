"""
The following serializers define the structure for data serialization and validation 
related to the User model and user authentication.
"""
# Import necessary modules and classes
from rest_framework import serializers
from .models import User
from django.core.exceptions import ValidationError

# Serializer for the User model
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    
    - Defines the structure for serializing User model fields.
    - Specifies the fields to be serialized.
    - Sets 'write_only' attribute for the password field to ensure it's not included in responses.
    """
    class Meta:
        model = User
        # Define fields to be serialized
        fields = ['id', 'fname', 'lname', 'username', 'password', 'birthdate', 'email', 'phone', 'gender', 'chronic_disease', 'image']
        # Specify extra kwargs for fields
        extra_kwargs = {'password': {'write_only': True}}

# Serializer for user login
class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    - Defines the structure for serializing user login data.
    - Includes fields for username/email and password.
    """
    # Field for username or email (maximum length: 255 characters)
    username_or_email = serializers.CharField(max_length=255)
    # Field for password (write-only)
    password = serializers.CharField(write_only=True)
    
# Serializer for user authentication token
class AuthTokenSerializer(serializers.Serializer):
    """
    Serializer for user authentication token.
    
    - Defines the structure for serializing user authentication data.
    - Includes fields for email and password, with password input type set to 'password'.
    """
    # Field for email (must be a valid email)
    email = serializers.EmailField()
    # Field for password (with style for input type password, trim_whitespace set to False)
    password = serializers.CharField(style={'input_type': 'password'},
                                     trim_whitespace=False)

# Serializer for password reset request
class PasswordResetRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for password reset request.
    
    - Defines the structure for serializing password reset requests.
    - Includes a field for the user's email.
    """
    class Meta:
        model = User
        # Define fields to be serialized
        fields = ['email']

# Serializer for updating user password
class PasswordUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating user password.
    
    - Defines the structure for serializing data required to update user passwords.
    - Includes a field for the new password.
    - Overrides the 'update' method to set the new password and save the instance.
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
    
class ResendEmailVerificationSerializer(serializers.Serializer):
    # Dummy serializer class to satisfy DRF's requirements
    pass