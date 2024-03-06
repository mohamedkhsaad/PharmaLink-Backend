"""
A file to define a custom token authentication system for our project

"""
from django.contrib.auth.backends import BaseBackend
from rest_framework.authentication import TokenAuthentication
from User.models import CustomToken
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from .models import CustomToken
from django.contrib.auth import get_user_model
# User = get_user_model()
class CustomTokenAuthentication(BaseAuthentication):
    keyword = 'PatientCustomToken'
    def authenticate(self, request):
        auth_header = get_authorization_header(request).split()
        # print(f"auth header: {auth_header}")
        if not auth_header or auth_header[0].lower() != self.keyword.lower().encode():
            return None
        if len(auth_header) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise AuthenticationFailed(msg)
        elif len(auth_header) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise AuthenticationFailed(msg)
        try:
            token = auth_header[1].decode()
            custom_token = CustomToken.objects.get(key=token)
        except CustomToken.DoesNotExist:
            raise AuthenticationFailed('Invalid token')
        user_email = custom_token.email
        User = get_user_model()

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid user')
        return (user, custom_token)
    
    def authenticate_header(self, request):
        return self.keyword

