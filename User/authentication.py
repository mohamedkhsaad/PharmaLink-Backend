"""
The following class defines a custom token authentication mechanism.
"""

# Import necessary modules and classes
from django.contrib.auth.backends import BaseBackend
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from .models import CustomToken
from django.contrib.auth import get_user_model

# Custom token authentication class
class CustomTokenAuthentication(BaseAuthentication):
    """
    Custom token authentication class.
    
    - Extends BaseAuthentication to implement custom token-based authentication logic.
    - Defines a keyword used for token authentication in the HTTP header.
    - Implements the authenticate() method to authenticate the user based on the provided token.
    - Checks the authorization header for the presence of the custom token keyword.
    - Decodes and retrieves the token from the header, then validates it against stored custom tokens.
    - Retrieves the associated user based on the token's email.
    - Raises AuthenticationFailed exceptions for various error scenarios, such as invalid token header, missing credentials, invalid token, or invalid user.
    - Implements the authenticate_header() method to specify the authentication header keyword.
    """
    keyword = 'PatientCustomToken'

    def authenticate(self, request):
        """
        Method to authenticate the user based on the provided token.
        """
        auth_header = get_authorization_header(request).split()
        if not auth_header or auth_header[0].lower() != self.keyword.lower().encode():
            # No token provided or invalid token header
            return None

        if len(auth_header) == 1:
            # Invalid token header. No credentials provided.
            raise AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth_header) > 2:
            # Invalid token header. Token string should not contain spaces.
            raise AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        try:
            # Decode and retrieve the token from the header
            token = auth_header[1].decode()
            custom_token = CustomToken.objects.get(key=token)
        except CustomToken.DoesNotExist:
            # Invalid token
            raise AuthenticationFailed('Invalid token')

        # Retrieve user based on the token's email
        user_email = custom_token.email
        User = get_user_model()
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            # Invalid user
            raise AuthenticationFailed('Invalid user')

        # Return the authenticated user and the custom token
        return (user, custom_token)
    
    def authenticate_header(self, request):
        """
        Method to specify the authentication header keyword.
        """
        return self.keyword
