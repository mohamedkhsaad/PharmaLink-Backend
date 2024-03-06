"""
A file to define a custom token authentication system for our project
"""
from django.contrib.auth.backends import BaseBackend
from rest_framework.authentication import TokenAuthentication
from Doctor.models import CustomToken
from Doctor.models import Doctor
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
class DoctorCustomTokenAuthentication(BaseAuthentication):
    keyword = 'DoctorCustomToken'
    def authenticate(self, request):
        auth_header = get_authorization_header(request).split()
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
        doctor_email = custom_token.email
        try:
            doctor = Doctor.objects.get(email=doctor_email)
        except Doctor.DoesNotExist:
            raise AuthenticationFailed('Invalid doctor')
        return (doctor, custom_token)
    def authenticate_header(self, request):
        return self.keyword