"""
The following views implement various functionalities related to users in the application.
"""
# Import necessary modules and classes
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from User.models import *
from User.serializers import *
from rest_framework.authtoken.models import Token
from User.authentication import CustomToken
from rest_framework.views import APIView
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import gettext as _
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from User.authentication import *
from rest_framework.generics import GenericAPIView
import smtplib
from email.mime.text import MIMEText
from django.core.mail import send_mail
from rest_framework.generics import UpdateAPIView
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken

# View for user signup
class UserSignupView(generics.CreateAPIView):
    """
    This view allows users to sign up by providing their details.
    Upon successful signup, a verification email is sent to the user's provided email address.
    
    - Handles HTTP POST requests to create a new user account.
    - Validates user input data using the UserSerializer.
    - Checks for existing usernames and emails to prevent duplicates.
    - Upon successful signup, sends a verification email containing a verification link.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def send_custom_email(self, user_id, email):
        """
        Sends a custom verification email to the user's provided email address.
        """
        # Compose email message
        subject = 'Verify Your Email'
        # verification_link = f"https://127.0.0.1:8000/user/verify/{user_id}/"
        verification_link = f"https://54.234.91.4:8000/user/verify/{user_id}/"
        message = f'Click the following link to verify your email: {verification_link}'
        sender_email = 'pharmalink1190264@gmail.com'
        receiver_email = email
        
        # Construct email object
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email
        
        # Send email
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender_email, "azuk ngik jmqo udcb")
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            print("Email sent successfully.")
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def create(self, request, *args, **kwargs):
        """
        Handles user signup requests.
        Checks for existing username and email.
        Sends verification email upon successful signup.
        """
        # Check if the username is already taken
        existing_username = User.objects.filter(username=request.data.get('username')).first()
        if existing_username:
            return Response({"error": "Username is already taken. Please choose a different one."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if the email is already taken
        existing_email = User.objects.filter(email=request.data.get('email')).first()
        if existing_email:
            return Response({"error": "An account with that email address already exists. Please log in to continue."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # Save new user
            user = serializer.save()
            # Send verification email
            self.send_custom_email(user.id, user.email)
            response_data = {
                'id': user.id,
                'username':user.username
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View for resend email verification for doctors
class ResendEmailVerificationView(generics.GenericAPIView):
    """
    Resend email verification to a user's email address without updating the verification status.
    """

    serializer_class = ResendEmailVerificationSerializer  # Dummy serializer class

    def send_custom_email(self, user_id, email):
        """
        Sends a custom verification email to the user's provided email address.
        """
        subject = 'Verify Your Email'
        # verification_link = f"https://127.0.0.1:8000/user/verify/{user_id}/"
        verification_link = f"https://54.234.91.4:8000/user/verify/{user_id}/"
        message = f'Click the following link to verify your email: {verification_link}'
        sender_email = 'pharmalink1190264@gmail.com'
        receiver_email = email

        # Construct email object
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email

        # Send email
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender_email, "azuk ngik jmqo udcb")
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            print("Email sent successfully.")
        except Exception as e:
            print(f"Error sending email: {e}")

    def post(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        if user_id is None:
            return Response({"error": "Parameter 'user_id' is missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)

            # Resend verification email
            self.send_custom_email(user_id, user.email)

            return Response({"message": "Verification email resent successfully."}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
     
# View for email verification
class EmailVerificationView(APIView):
    """
    This view handles email verification requests.
    
    - Handles HTTP GET requests to mark the user's email as verified.
    - Requires the user ID in the URL to identify the user.
    - Sets the 'is_verified' flag to True in the User model.
    """
    def get(self, request, user_id):
        """
        Handles GET requests for email verification.
        Marks the user with the provided user ID as verified.
        """
        # Retrieve user object or return 404 if not found
        user = get_object_or_404(User, pk=user_id)
        
        # Mark user as verified
        user.is_verified = True
        user.save()
        
        # Respond with success message
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)

# # View for user login
# class CustomTokenLoginView(APIView):
#     """
#     This view handles user login using custom tokens.
    
#     - Handles HTTP POST requests for user login.
#     - Validates user credentials (email and password).
#     - Generates a custom token for authenticated users.
#     - Checks if the user's email is verified before allowing login.
#     """
#     serializer_class = AuthTokenSerializer

#     def post(self, request, format=None):
#         """
#         Handles user login requests.
#         Validates the provided credentials and generates a custom token for authenticated users.
#         """
#         # Validate serializer
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         # Retrieve email and password from request data
#         provided_email = request.data.get('email', '')
#         password = request.data.get('password')

#         # Attempt to retrieve user with provided email (case-insensitive lookup)
#         user = User.objects.filter(email__iexact=provided_email).first()

#         if not user:
#             # Return error response if user does not exist
#             return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

#         # Check if user's email is verified
#         if not user.is_verified:
#             return Response({'error': _('Email not verified')}, status=status.HTTP_401_UNAUTHORIZED)

#         # Validate password
#         if password == user.password:
#             # Generate custom token for authenticated user
#             custom_token = CustomToken.objects.create(user=user)
#             user_id = user.id
#             # Construct response data
#             response_data = {
#                 'id': user_id,
#                 'username': user.username,
#                 'email': provided_email,  # Return the provided email as is
#                 'token': custom_token.key
#             }
#             # Return success response with user data and token
#             return Response(response_data, status=status.HTTP_200_OK)
#         else:
#             # Return error response if password is incorrect
#             return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# View for user login
class CustomTokenLoginView(APIView):
    """
    This view handles user login using custom tokens.
    
    - Handles HTTP POST requests for user login.
    - Validates user credentials (email and password).
    - Generates a custom token for authenticated users.
    - Checks if the user's email is verified before allowing login.
    """

    serializer_class = AuthTokenSerializer

    def post(self, request, format=None):
        """
        Handle user login requests and generate tokens.
        """

        # Validate serializer data
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Retrieve email and password from request data
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')

        # Get user by filtering email case-insensitively
        user = User.objects.filter(email__iexact=email).first()

        # Check if user exists and password matches
        if user is None or password != user.password:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the user's email is verified
        if not user.is_verified:
            return Response({'error': 'Email not verified'}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate refresh token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Create or update CustomToken instance with tokens
        custom_token, created = CustomToken.objects.update_or_create(
            user=user,
            defaults={
                'refresh_token': str(refresh),
                'access_token': access_token,
            }
        )

        # Construct response data with user details and tokens
        response_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'refresh_token': str(refresh),
            'access_token': access_token,
        }
        return Response(response_data, status=status.HTTP_200_OK)

# View for refresh an access token using a refresh token
class RefreshTokenView(APIView):
    """
    View to refresh an access token using a refresh token.
    
    - Handles HTTP POST requests to refresh an access token.
    - Validates the refresh token provided in the request.
    - Retrieves the associated CustomToken object using the refresh token.
    - Updates the access token in the CustomToken object with the new one.
    """

    def post(self, request):
        """
        Handle POST requests to refresh an access token.
        """

        # Get the refresh token from the request data
        refresh_token_value = request.data.get('refresh_token')
        if not refresh_token_value:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the CustomToken object using the refresh token
        try:
            custom_token = CustomToken.objects.get(refresh_token=refresh_token_value)
        except CustomToken.DoesNotExist:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the refresh token
        try:
            refresh = RefreshToken(refresh_token_value)
            access_token = str(refresh.access_token)
        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the access token in the CustomToken object
        custom_token.access_token = access_token
        custom_token.save()

        return Response({'access_token': access_token}, status=status.HTTP_200_OK)
    
# View for user logout
class UserLogoutView(APIView):
    """
    This view logs out the user by deleting associated tokens.
    
    - Handles HTTP POST requests for user logout.
    - Requires user authentication using custom token authentication.
    - Deletes all tokens associated with the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        """
        Handles user logout requests.
        Deletes all tokens associated with the authenticated user.
        """
        # Retrieve the user's ID
        user_id = request.user.id

        try:
            # Delete all tokens associated with the user
            CustomToken.objects.filter(user_id=user_id).delete()            
            return Response({'message': 'Logout successful', 'user_id': user_id}, status=status.HTTP_200_OK)
        except CustomToken.DoesNotExist:
            # Return error response if no tokens found for the user
            return Response({'error': 'No tokens found for the user'}, status=status.HTTP_400_BAD_REQUEST)
        
# View for updating user profile
class UserUpdateView(generics.UpdateAPIView):
    """
    This view allows authenticated users to update their profile information.
    
    - Handles HTTP PUT requests to update user profile information.
    - Requires user authentication using custom token authentication.
    - Retrieves the authenticated user object.
    - Validates and updates user data using the UserSerializer.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def get_object(self):
        """
        Retrieves the authenticated user object.
        """
        return self.request.user

    def update(self, request, *args, **kwargs):
        """
        Handles user profile update requests.
        """
        # Determine if the update is partial or full
        partial = kwargs.pop('partial', False)
        
        # Retrieve the authenticated user object
        instance = self.get_object()
        
        # Validate and update user data
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return updated user data
        return Response(serializer.data)

    def perform_update(self, serializer):
        """
        Saves the updated user data.
        """
        serializer.save()

# View for password reset request
class PasswordResetRequestView(GenericAPIView):
    """
    This view allows users to request a password reset by providing their email address.
    Upon successful request, a password reset email is sent to the user's provided email address.
    
    - Handles HTTP POST requests for password reset requests.
    - Validates the email provided by the user.
    - Sends a password reset email containing a reset link to the user's email address.
    """
    serializer_class = PasswordResetRequestSerializer

    def send_password_reset_email(self, user):
        """
        Sends a password reset email to the user's provided email address.
        """
        subject = 'Reset Your Password'
        # reset_link = f"https://127.0.0.1:8000/user/reset-password/{user.id}/"
        reset_link = f"https://54.234.91.4:8000/user/reset-password/{user.id}/"

        message = f'Click the following link to reset your password: {reset_link}'
        sender_email = 'pharmalink1190264@gmail.com'
        receiver_email = user.email
        
        # Construct email object
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = user.email
        
        # Send email
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender_email, "azuk ngik jmqo udcb")
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            print("Email sent successfully.")
        except Exception as e:
            print(f"Error sending email: {e}")

    def post(self, request, *args, **kwargs):
        """
        Handles password reset requests.
        Sends a password reset email to the user's provided email address.
        """
        # Retrieve email from request data
        email = request.data.get('email')
        
        if email:
            try:
                # Attempt to retrieve user with provided email
                user = User.objects.get(email=email)
                # Send password reset email
                self.send_password_reset_email(user)
                return Response({"message": "Password reset email sent successfully."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                # Return error response if user does not exist
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Return error response if email is not provided
            return Response({"error": "Email not provided."}, status=status.HTTP_400_BAD_REQUEST)    
    # email validation error
    # def post(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     if serializer.is_valid():
    #         email = serializer.validated_data['email']
    #         user = User.objects.get(email=email)
    #         self.send_password_reset_email(user)
    #         return Response({"message": "Password reset email sent successfully."}, status=status.HTTP_200_OK)
    #     else:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View for password reset
class PasswordResetView(UpdateAPIView):
    """
    This view allows any user to reset their password.
    
    - Handles HTTP PUT requests for password reset.
    - Validates the new password provided by the user.
    - Updates the user's password in the database upon successful validation.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]  # Allow any user to reset their password
    serializer_class = PasswordUpdateSerializer  # Create a serializer for resetting the password

    def get_object(self):
        """
        Retrieves the user object based on the user_id provided in the URL.
        """
        user_id = self.kwargs.get('user_id')
        return User.objects.get(pk=user_id)

    def update(self, request, *args, **kwargs):
        """
        Handles password reset requests.
        Validates the new password and updates the user's password.
        """
        # Get the user object
        user = self.get_object()
        
        # Retrieve the new password from request data
        new_password = request.data.get('password')
        
        if new_password:
            # Validate the new password
            if not any(char.islower() for char in new_password):
                return Response({"error": "Password must contain at least one lowercase letter."}, status=status.HTTP_400_BAD_REQUEST)
            if not any(char.isupper() for char in new_password):
                return Response({"error": "Password must contain at least one uppercase letter."}, status=status.HTTP_400_BAD_REQUEST)
            if not any(char.isdigit() for char in new_password):
                return Response({"error": "Password must contain at least one digit."}, status=status.HTTP_400_BAD_REQUEST)
            if not any(char in "!@#$%^&*()_+{}[];:<>,./?" for char in new_password):
                return Response({"error": "Password must contain at least one special character."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update the user's password
            user.password = new_password
            user.save()
            
            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        else:
            # Return error response if new password is not provided
            return Response({"error": "New password not provided."}, status=status.HTTP_400_BAD_REQUEST)

# View for retrieving user information
class UserInfoView(APIView):
    """
    This view retrieves user information based on the provided user ID.
    
    - Handles HTTP GET requests to retrieve user information.
    - Requires the user ID in the URL to identify the user.
    - Retrieves user data from the User model and serializes it using the UserSerializer.
    """
    def get(self, request, user_id):
        """
        Handles GET requests to retrieve user information.
        """
        try:
            # Retrieve user object based on the provided user ID
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # Return error response if user does not exist
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize user data and return response
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
