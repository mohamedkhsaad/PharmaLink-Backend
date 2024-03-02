from django.shortcuts import render
# Create your views here.
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

# ssl error
# class UserSignupView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer

#     def create(self, request, *args, **kwargs):
#         # Check if the username is already taken
#         existing_username = User.objects.filter(username=request.data.get('username')).first()
#         if existing_username:
#             return Response({"error": "Username is already taken. Please choose a different one."},
#                             status=status.HTTP_400_BAD_REQUEST)
#         # Check if the email is already taken
#         existing_email = User.objects.filter(email=request.data.get('email')).first()
#         if existing_email:
#             return Response({"error": "An account with that email address already exists. Please log in to continue."},
#                             status=status.HTTP_400_BAD_REQUEST)
#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             # Send verification email
#             verification_link = f"https://PharmaLink.com/verify/{User.id}/"
#             subject = 'Verify Your Email'
#             message = f'Click the following link to verify your email: {verification_link}'
#             from_email = 'pharmalink1190264@gmail.com'
#             to_email = [User.email]
#             send_mail(subject, message, from_email, to_email)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserSignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    def send_custom_email(self, user_id, email):
        subject = 'Verify Your Email'
        verification_link = f"https://127.0.0.1:8000/user/verify/{user_id}/"
        message = f'Click the following link to verify your email: {verification_link}'
        sender_email = 'pharmalink1190264@gmail.com'
        receiver_email = email
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender_email, "azuk ngik jmqo udcb")
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            print("Email sent successfully.")
        except Exception as e:
            print(f"Error sending email: {e}")
    def create(self, request, *args, **kwargs):
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
            user = serializer.save()
            # Send verification email using custom logic
            self.send_custom_email(user.id, user.email)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class EmailVerificationView(APIView):
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        user.is_verified = True
        user.save()
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)

class CustomTokenLoginView(APIView):
    '''
    This is a view class for the user login. User has to verify his email after signup to be able to login
    '''
    serializer_class = AuthTokenSerializer
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)  # Validate the serializer
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_verified:
            return Response({'error': _('Email not verified')}, status=status.HTTP_401_UNAUTHORIZED)
        if password == user.password:
            custom_token = CustomToken.objects.create(user=user)
            user_id = user.id
            response_data = {
                'id': user_id,
                'email': user.email,
                'token': custom_token.key,
                'first_name': user.fname,
                'last_name': user.lname,
                'initials': (user.fname[0] if user.fname else '') + (user.lname[0] if user.lname else '')
            }
            response_data['initials'] = response_data['initials'].upper()
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)




class UserLogoutView(APIView):
    """
    This view logs out the user by deleting all associated tokens.
    """
    permission_classes = [IsAuthenticated]
    # authentication_classes = [CustomTokenAuthentication]
    def post(self, request, format=None):
        # Retrieve the user's ID
        user_id = request.user.id
        # Delete all tokens associated with the user
        try:
            CustomToken.objects.filter(user_id=user_id).delete()            
            return Response({'message': 'Logout successful', 'user_id': user_id}, status=status.HTTP_200_OK)
        except CustomToken.DoesNotExist:
            return Response({'error': 'No tokens found for the user'}, status=status.HTTP_400_BAD_REQUEST)
class UserUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]
    def get_object(self):
        return self.request.user
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    def perform_update(self, serializer):
        serializer.save()

class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    def send_password_reset_email(self,user):
        subject = 'Reset Your Password'
        reset_link = f"https://127.0.0.1:8000/user/reset-password/{user.id}/"
        message = f'Click the following link to reset your password: {reset_link}'
        sender_email = 'pharmalink1190264@gmail.com'
        receiver_email = user.email
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = user.email
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender_email, "azuk ngik jmqo udcb")
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            print("Email sent successfully.")
        except Exception as e:
            print(f"Error sending email: {e}")
    def post(self, request, *args, **kwargs):
        # serializer = self.serializer_class(data=request.data)
        # serializer.is_valid(raise_exception=True)  # Validate the serializer
        email = request.data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                self.send_password_reset_email(user)
                return Response({"message": "Password reset email sent successfully."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
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

class PasswordResetView(UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]  # Allow any user to reset their password
    serializer_class = PasswordUpdateSerializer  # Create a serializer for resetting the password
    def get_object(self):
        # Get the user object based on the user_id provided in the URL
        user_id = self.kwargs.get('user_id')
        return User.objects.get(pk=user_id)
    def update(self, request, *args, **kwargs):
        # Get the user object
        user = self.get_object()
        # Update the password
        new_password = request.data.get('password')
        print(new_password)
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
            # user.set_password(new_password)
            user.save()
            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "New password not provided."}, status=status.HTTP_400_BAD_REQUEST)



class UserInfoView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)