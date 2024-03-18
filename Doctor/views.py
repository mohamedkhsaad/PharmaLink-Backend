"""
The following views implement various functionalities related to doctors in the application.
"""
# Import necessary modules and classes
from django.shortcuts import render
from django.shortcuts import render
# Create your views here.
from rest_framework import generics, status
from rest_framework.response import Response
from Doctor.models import *
from Doctor.serializers import *
from Doctor.authentication import DoctorCustomTokenAuthentication
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
from django.core.exceptions import ObjectDoesNotExist

# Define the DoctorSignupView class
class DoctorSignupView(generics.CreateAPIView):
    """
    DoctorSignupView class for handling doctor signup requests.
    
    - Inherits from generics.CreateAPIView to handle HTTP POST requests for creating a new doctor account.
    - Defines queryset and serializer_class attributes for database operations and serialization.
    - Implements a custom method send_custom_email() to send a verification email to the doctor's provided email address.
    - Overrides the create() method to perform custom validation and logic for doctor signup.
    """

    # Specify the queryset for retrieving Doctor objects
    queryset = Doctor.objects.all()

    # Specify the serializer class for serializing and validating Doctor objects
    serializer_class = DoctorSerializer

    def send_custom_email(self, doctor_id, email):
        """
        Sends a custom verification email to the doctor's provided email address.
        """
        # Define email parameters
        subject = 'Verify Your Email'
        verification_link = f"https://127.0.0.1:8000/doctor/verify/{doctor_id}/"
        message = f'Click the following link to verify your email: {verification_link}'
        sender_email = 'pharmalink1190264@gmail.com'
        receiver_email = email

        # Construct email message
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = receiver_email

        try:
            # Connect to SMTP server and send email
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender_email, "azuk ngik jmqo udcb")
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            print("Email sent successfully.")
        except Exception as e:
            # Handle error if email sending fails
            print(f"Error sending email: {e}")

    def create(self, request, *args, **kwargs):
        """
        Create a new doctor account.
        """
        # Check if the username is already taken
        existing_username = Doctor.objects.filter(username=request.data.get('username')).first()
        if existing_username:
            # Return error response if username is already taken
            return Response({"error": "Username is already taken. Please choose a different one."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if the email is already taken
        existing_email = Doctor.objects.filter(email=request.data.get('email')).first()
        if existing_email:
            # Return error response if email is already associated with an account
            return Response({"error": "An account with that email address already exists. Please log in to continue."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Serialize the request data
        serializer = DoctorSerializer(data=request.data)
        
        if serializer.is_valid():
            # Save the doctor object
            doctor = serializer.save()
            # Send verification email using custom logic
            self.send_custom_email(doctor.id, doctor.email)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # Return error response if serializer is not valid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Doctor login view class
class DoctorCustomTokenLoginView(APIView):
    """
    View class for doctor login. Doctor has to verify their email after signup to be able to login.
    
    - Inherits from APIView to handle HTTP request methods.
    - Defines the serializer class for doctor authentication.
    - Implements the POST method to handle doctor login requests.
    - Validates the provided credentials and generates a custom token for authenticated doctors.
    - Retrieves the doctor object using the provided email and verifies the email status.
    - Compares the provided password with the stored password for authentication.
    - Generates or retrieves the custom token associated with the doctor upon successful authentication.
    - Prepares and returns a response with user data and token upon successful authentication.
    - Returns error responses for various scenarios, such as invalid credentials or unverified email.
    """
    serializer_class = DoctorAuthTokenSerializer

    def post(self, request, format=None):
        # Serialize the request data
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)  # Validate the serializer

        # Extract email and password from request data
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            # Retrieve the doctor object using the provided email
            doctor = Doctor.objects.get(email=email)
        except Doctor.DoesNotExist:
            # Return error response if doctor with provided email does not exist
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the doctor's email is verified
        if not doctor.is_verified:
            # Return error response if doctor's email is not verified
            return Response({'error': _('Email not verified')}, status=status.HTTP_401_UNAUTHORIZED)

        # Compare the provided password with the doctor's password
        if password == doctor.password:
            # Create or retrieve the custom token associated with the doctor
            custom_token, created = CustomToken.objects.get_or_create(doctor=doctor)

            # Prepare response data
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

            # Return success response with user data and token
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            # Return error response if provided credentials are invalid
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
# View for retrieving doctor information
class DoctorInfoView(APIView):
    """
    View class to retrieve information about a specific doctor.

    - Inherits from APIView to handle HTTP request methods.
    - Implements the GET method to retrieve information about a specific doctor.
    - Allows retrieval of information about a doctor based on the provided doctor ID.
    - Retrieves the doctor object with the provided ID from the database.
    - Returns an error response if the doctor with the provided ID does not exist.
    - Serializes the retrieved doctor object to convert it into JSON format.
    - Returns a response with serialized doctor data in the HTTP response body.
    """

    def get(self, request, doctor_id):
        # Retrieve the doctor object with the provided ID
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            # Return error response if doctor with the provided ID does not exist
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize the doctor object
        serializer = DoctorSerializer(doctor)
        
        # Return serialized doctor data in the response
        return Response(serializer.data, status=status.HTTP_200_OK)

# View for email verification for doctors
class DoctorEmailVerificationView(APIView):
    """
    View class to handle email verification for doctors.

    - Inherits from APIView to handle HTTP request methods.
    - Implements the GET method to handle email verification for doctors.
    - Retrieves the doctor object with the provided ID from the database or returns a 404 error if not found.
    - Sets the is_verified flag of the doctor object to True to mark the email address as verified.
    - Saves the updated doctor object with the verified email address.
    - Returns a success message indicating that the email has been verified successfully.
    """

    def get(self, request, doctor_id):
        # Retrieve the doctor object with the provided ID or return a 404 error if not found
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        
        # Set the is_verified flag to True and save the doctor object
        doctor.is_verified = True
        doctor.save()
        
        # Return a success message in the response
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)

# View for resend email verification for doctors
class DoctorResendEmailVerificationView(generics.GenericAPIView):
    """
    Resend email verification to a user's email address without updating the verification status.
    """

    serializer_class = DoctorResendEmailVerificationSerializer  # Dummy serializer class

    def send_custom_email(self, doctor_id, email):
        """
        Sends a custom verification email to the user's provided email address.
        """
        subject = 'Verify Your Email'
        verification_link = f"https://127.0.0.1:8000/user/verify/{doctor_id}/"
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
        doctor_id = request.query_params.get('doctor_id')
        if doctor_id is None:
            return Response({"error": "Parameter 'doctor_id' is missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doctor = Doctor.objects.get(id=doctor_id)

            # Resend verification email
            self.send_custom_email(doctor_id, doctor.email)

            return Response({"message": "Verification email resent successfully."}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

# View for doctor logout
class DoctorLogoutView(APIView):
    """
    View class to handle doctor logout by deleting associated tokens.

    - Inherits from APIView to handle HTTP request methods.
    - Specifies the permission_classes to restrict access to authenticated doctors only.
    - Specifies the authentication_classes to use DoctorCustomTokenAuthentication for authentication.
    - Implements the POST method to handle doctor logout requests.
    - Retrieves the doctor's ID from the authenticated request.
    - Deletes all tokens associated with the doctor's session using CustomToken model's filter method.
    - Returns a success message indicating that the logout was successful along with the doctor's ID in the response.
    - Handles the case where no tokens are found for the doctor and returns an error message accordingly.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def post(self, request, format=None):
        # Retrieve the doctor's ID from the authenticated request
        doctor_id = request.user.id
        
        # Delete all tokens associated with the doctor
        try:
            CustomToken.objects.filter(doctor_id=doctor_id).delete()
            # Return success message in the response
            return Response({'message': 'Logout successful', 'doctor_id': doctor_id}, status=status.HTTP_200_OK)
        except CustomToken.DoesNotExist:
            # Return error message if no tokens found for the doctor
            return Response({'error': 'No tokens found for the doctor'}, status=status.HTTP_400_BAD_REQUEST)
        
# View for updating doctor profile
class DoctorUpdateView(generics.UpdateAPIView):
    """
    View class to handle updating doctor profile information.

    - Inherits from generics.UpdateAPIView to provide a generic view for updating objects via HTTP PUT method.
    - Specifies the queryset to include all Doctor objects for updating.
    - Specifies the serializer_class to use Doctorserialzer for serializing and deserializing doctor data.
    - Specifies the permission_classes to ensure that only authenticated doctors can update their profiles.
    - Specifies the authentication_classes to use DoctorCustomTokenAuthentication for authentication.
    - Overrides the get_object method to retrieve the currently authenticated doctor object.
    - Overrides the update method to handle updating doctor profile information.
    - Handles partial updates if 'partial' is set to True.
    - Performs validation on the serializer and raises an exception if validation fails.
    - Calls the perform_update method to save the updated data.
    - Overrides the perform_update method to save the updated serializer data.
    """
    
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated
    authentication_classes = [DoctorCustomTokenAuthentication]  # Use custom token authentication

    def get_object(self):
        """
        Get the currently authenticated doctor object.
        """
        return self.request.user

    def update(self, request, *args, **kwargs):
        """
        Handle updating doctor profile information.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """
        Perform the update operation on the doctor object.
        """
        serializer.save()

# View for handling password reset requests for doctors
class DoctorPasswordResetRequestView(GenericAPIView):
    """
    View class to handle password reset requests for doctors.

    - Inherits from GenericAPIView to provide a generic view for handling password reset requests.
    - Specifies the serializer_class to use DoctorPasswordResetRequestSerializer for serializing and deserializing data.
    - Defines the send_password_reset_email method to send a password reset email to the specified doctor.
    - Handles POST requests to send password reset emails.
    - Retrieves the doctor by email from the request data.
    - Sends a password reset email to the doctor if the email is provided and the doctor exists.
    - Returns appropriate responses based on the outcome of the password reset email sending process.
    """

    serializer_class = DoctorPasswordResetRequestSerializer

    def send_password_reset_email(self, doctor):
        """
        Sends a password reset email to the specified doctor.
        """
        # Compose email content
        subject = 'Reset Your Password'
        reset_link = f"https://127.0.0.1:8000/doctor/reset-password/{doctor.id}/"
        message = f'Click the following link to reset your password: {reset_link}'

        # Set email parameters
        sender_email = 'pharmalink1190264@gmail.com'
        receiver_email = doctor.email
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = doctor.email

        # Attempt to send email
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
        Handle POST requests to send password reset emails.
        """
        email = request.data.get('email')
        if email:
            # Retrieve doctor by email and send reset email
            try:
                doctor = Doctor.objects.get(email=email)
                self.send_password_reset_email(doctor)
                return Response({"message": "Password reset email sent successfully."}, status=status.HTTP_200_OK)
            except Doctor.DoesNotExist:
                return Response({"error": "Doctor with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "Email not provided."}, status=status.HTTP_400_BAD_REQUEST)
    
# View for handling password resets for doctors
class DoctorPasswordResetView(UpdateAPIView):
    """
    View class to handle password resets for doctors.

    - Inherits from UpdateAPIView to provide a view for updating doctor information.
    - Defines the queryset to include all Doctor objects.
    - Specifies permission_classes to allow any user to reset their password.
    - Specifies serializer_class as DoctorPasswordUpdateSerializer for serializing and deserializing data.
    - Implements the get_object method to retrieve the doctor object based on the doctor_id provided in the URL.
    - Overrides the update method to handle password reset requests.
    - Retrieves the doctor object.
    - Validates the new password provided in the request data against complexity rules.
    - Checks if the new password meets the required complexity criteria:
    - Contains at least one lowercase letter.
    - Contains at least one uppercase letter.
    - Contains at least one digit.
    - Contains at least one special character.
    - Updates the doctor's password if the new password is valid.
    - Returns appropriate responses based on the outcome of the password reset process.
    """

    queryset = Doctor.objects.all()
    permission_classes = [AllowAny]  # Allow any user to reset their password
    serializer_class = DoctorPasswordUpdateSerializer  # Serializer for resetting the password

    def get_object(self):
        """
        Get the doctor object based on the doctor_id provided in the URL.
        """
        user_id = self.kwargs.get('user_id')
        return Doctor.objects.get(pk=user_id)

    def update(self, request, *args, **kwargs):
        """
        Handle password reset requests.
        """
        # Get the doctor object
        doctor = self.get_object()

        # Get the new password from the request data
        new_password = request.data.get('password')

        # Validate the new password
        if new_password:
            if not any(char.islower() for char in new_password):
                return Response({"error": "Password must contain at least one lowercase letter."},
                                status=status.HTTP_400_BAD_REQUEST)
            if not any(char.isupper() for char in new_password):
                return Response({"error": "Password must contain at least one uppercase letter."},
                                status=status.HTTP_400_BAD_REQUEST)
            if not any(char.isdigit() for char in new_password):
                return Response({"error": "Password must contain at least one digit."},
                                status=status.HTTP_400_BAD_REQUEST)
            if not any(char in "!@#$%^&*()_+{}[];:<>,./?" for char in new_password):
                return Response({"error": "Password must contain at least one special character."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Update the doctor's password
            doctor.password = new_password
            doctor.save()

            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "New password not provided."}, status=status.HTTP_400_BAD_REQUEST)
        
# View for retrieving a doctor's phone number
class DoctorPhoneNumberView(APIView):
    """
    A view class to retrieve a doctor's phone number.

    - Inherits from APIView to create a view for handling HTTP GET requests.
    - Defines a get method to retrieve the phone number of a doctor based on the provided doctor ID.
    - Attempts to retrieve the doctor object with the given ID from the database.
    - If the doctor object is not found, returns a 404 Not Found response with an appropriate error message.
    - Retrieves the phone number of the doctor from the doctor object.
    - Returns a successful response with the doctor's phone number if the doctor is found.
    """

    def get(self, request, doctor_id):
        """
        Get the phone number of the doctor with the given ID.
        """
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            # If the doctor is not found, return a 404 response
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get the phone number of the doctor
        phone_number = doctor.phone
        
        # Return the phone number in the response
        return Response({'phone_number': phone_number}, status=status.HTTP_200_OK)