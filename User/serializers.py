from rest_framework import serializers
from .models import User
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','fname','lname','username', 'password', 'birthdate', 'email', 'phone', 'gender', 'chronic_disease']
        extra_kwargs = {'password': {'write_only': True}}

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True)
    
class AuthTokenSerializer(serializers.Serializer):
    """ 
    Serializer for the user auth Token
    """
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'},
                                     trim_whitespace=False)
    

class PasswordResetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']

class PasswordUpdateSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance