from django.shortcuts import render
from django.shortcuts import render
# Create your views here.
from rest_framework import generics, status
from rest_framework.response import Response
from Doctor.models import *
from Doctor.serializers import *
from Doctor.authentication import CustomTokenAuthentication
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
import smtplib
from email.mime.text import MIMEText
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from rest_framework.generics import GenericAPIView
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import AllowAny

# Create your views here.

class DoctorSignupView(generics.CreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = Doctorserialzer
    def send_custom_email(self, doctor_id, email):
        subject = 'Verify Your Email'
        verification_link = f"https://127.0.0.1:8000/doctor/verify/{doctor_id}/"
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
        existing_username = Doctor.objects.filter(username=request.data.get('username')).first()
        if existing_username:
            return Response({"error": "Username is already taken. Please choose a different one."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if the email is already taken
        existing_email = Doctor.objects.filter(email=request.data.get('email')).first()
        if existing_email:
            return Response({"error": "An account with that email address already exists. Please log in to continue."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = Doctorserialzer(data=request.data)
        if serializer.is_valid():
            doctor = serializer.save()
            # Send verification email using custom logic
            self.send_custom_email(doctor.id, doctor.email)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorCustomTokenLoginView(APIView):
    '''
    This is a view class for the user login. User has to verify his email after signup to be able to login
    '''
    serializer_class = DoctorAuthTokenSerializer
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)  # Validate the serializer
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            doctor = Doctor.objects.get(email=email)
        except Doctor.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not doctor.is_verified:
            return Response({'error': _('Email not verified')}, status=status.HTTP_401_UNAUTHORIZED)
        if password == doctor.password:
            custom_token, created = CustomToken.objects.get_or_create(doctor=doctor)
            user_id = doctor.id
            response_data = {
                'id': user_id,
                'email': doctor.email,
                'token': custom_token.key,
                'first_name': doctor.fname,
                'last_name': doctor.lname,
                'initials': (doctor.fname[0] if doctor.fname else '') + (doctor.lname[0] if doctor.lname else '')
            }
            response_data['initials'] = response_data['initials'].upper()
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
#DoctorEmailVerificationView
class DoctorEmailVerificationView(APIView):
    def get(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        doctor.is_verified = True
        doctor.save()
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)

class DoctorLogoutView(APIView):
    """
    This view logs out the user by deleting all associated tokens.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]
    def post(self, request, format=None):
        # Retrieve the doctor's ID
        doctor_id = request.user.id
        # Delete all tokens associated with the doctor
        try:
            CustomToken.objects.filter(doctor_id=doctor_id).delete()            
            return Response({'message': 'Logout successful', 'doctor_id': doctor_id}, status=status.HTTP_200_OK)
        except CustomToken.DoesNotExist:
            return Response({'error': 'No tokens found for the doctor'}, status=status.HTTP_400_BAD_REQUEST)

class DoctorUpdateView(generics.UpdateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = Doctorserialzer
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


class DoctorPasswordResetRequestView(GenericAPIView):
    serializer_class = DoctorPasswordResetRequestSerializer
    def send_password_reset_email(self,doctor):
        subject = 'Reset Your Password'
        reset_link = f"https://127.0.0.1:8000/doctor/reset-password/{doctor.id}/"
        message = f'Click the following link to reset your password: {reset_link}'
        sender_email = 'pharmalink1190264@gmail.com'
        receiver_email = doctor.email
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = doctor.email
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
                doctor = Doctor.objects.get(email=email)
                self.send_password_reset_email(doctor)
                return Response({"message": "Password reset email sent successfully."}, status=status.HTTP_200_OK)
            except Doctor.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "Email not provided."}, status=status.HTTP_400_BAD_REQUEST)
    


class PasswordResetView(UpdateAPIView):
    queryset = Doctor.objects.all()
    permission_classes = [AllowAny]  # Allow any user to reset their password
    serializer_class = DoctorPasswordUpdateSerializer  # Create a serializer for resetting the password
    def get_object(self):
        # Get the user object based on the user_id provided in the URL
        user_id = self.kwargs.get('user_id')
        return Doctor.objects.get(pk=user_id)
    def update(self, request, *args, **kwargs):
        # Get the user object
        doctor = self.get_object()
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
            # Update the doctors's password
            doctor.password = new_password
            # user.set_password(new_password)
            doctor.save()
            
            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "New password not provided."}, status=status.HTTP_400_BAD_REQUEST)
