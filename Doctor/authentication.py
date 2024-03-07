"""
A custom token authentication system for Doctor users in the project.
"""

# Import necessary modules and classes
from django.contrib.auth.backends import BaseBackend
from rest_framework.authentication import TokenAuthentication
from Doctor.models import CustomToken
from Doctor.models import Doctor
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

# Custom token authentication class for Doctor users
class DoctorCustomTokenAuthentication(BaseAuthentication):
    """
    Custom authentication class for Doctor users using custom tokens.

    - Inherits from BaseAuthentication provided by Django REST Framework.
    - Defines a keyword for identifying the authentication method in the request header.
    - Implements the authenticate method to authenticate users based on the provided custom token.
    - Raises AuthenticationFailed exceptions for various error scenarios.
    - Implements the authenticate_header method to specify the authentication header keyword.
    """

    keyword = 'DoctorCustomToken'

    def authenticate(self, request):
        """
        Method to authenticate Doctor users using custom tokens.

        - Retrieves the authorization header from the request.
        - Validates the format of the authorization header.
        - Retrieves the custom token from the header and verifies its validity.
        - Retrieves the associated Doctor instance based on the token's email.
        - Returns a tuple containing the authenticated Doctor instance and the custom token.

        Raises:
            AuthenticationFailed: If the token is invalid or associated Doctor does not exist.
        """

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
        """
        Method to specify the authentication header keyword.

        - Returns the keyword used to identify the custom token authentication method.

        Returns:
            str: The keyword used in the authentication header.
        """
        
        return self.keyword