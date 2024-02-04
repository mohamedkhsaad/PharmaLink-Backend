from django.shortcuts import render

# Create your views here.
from rest_framework import generics, status
from rest_framework.response import Response
from .models import User
from .serializers import *

from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db import models
from User.authentication import CustomToken
from rest_framework.views import APIView
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import gettext as _
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from User.authentication import *
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
    
import smtplib
from email.mime.text import MIMEText
from django.core.mail import send_mail
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer  # Replace with the actual import path for your UserSerializer

class UserSignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def send_custom_email(self, user_id, email):
        subject = 'Verify Your Email'
        verification_link = f"https://127.0.0.1:8000/verify/{user_id}/"
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
        print(user_id)

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