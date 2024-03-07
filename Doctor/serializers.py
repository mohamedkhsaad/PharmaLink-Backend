"""
The following serializers define how data is serialized and deserialized for Doctor-related models and authentication.
"""

# Import necessary modules and classes
from rest_framework import serializers
from Doctor.models import*

# Serializer for Doctor model
class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Doctor model.

    - Specifies the Doctor model as the model to be serialized.
    - Defines the fields to include in the serialization.
    - Adds extra kwargs to specify write-only for the password field.
    """

    class Meta:
        model=Doctor
        fields = ['id','fname','lname','username', 'password', 'birthdate', 'email', 'phone', 'gender','license_number','specialization','degree','graduation_date','university','image']
        extra_kwargs = {'password': {'write_only': True}}

# Serializer for Doctor authentication token
class DoctorAuthTokenSerializer(serializers.Serializer):
    """
    Serializer for the Doctor authentication token.

    - Provides fields for email and password for authentication.
    - Specifies the email field as an EmailField and the password field as a CharField.
    - Defines the input type for the password field as 'password'.
    """

    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'},
                                     trim_whitespace=False)
    
# Serializer for Doctor password reset request
class DoctorPasswordResetRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for the Doctor password reset request.

    - Specifies the Doctor model as the model to be used for password reset.
    - Includes only the email field for password reset requests.
    """    
    
    class Meta:
        model = Doctor
        fields = ['email']

# Serializer for updating Doctor password
class DoctorPasswordUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating Doctor password.

    - Provides a single field for the new password.
    - Specifies the field as write-only and required.
    - Defines a method to update the Doctor's password.
    """    
    
    password = serializers.CharField(write_only=True, required=True)

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance