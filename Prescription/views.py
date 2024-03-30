"""
The following views implement various functionalities related to prescriptions in the application.
"""
# Import necessary modules and classes
from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import DrugEye
from .serializers import UserSerializerEmail
from .serializers import DrugEyeSerializer
from .models import *

from User.authentication import CustomTokenAuthentication
from User.models import User

from Doctor.models import Doctor
from Doctor.serializers import DoctorSerializer
from Doctor.authentication import DoctorCustomTokenAuthentication

from .utils import generate_session_id, generate_otp, validate_session, send_otp,send_custom_email_otp
from django.utils import timezone
from datetime import timedelta
from .serializers import PrescriptionSerializer

import json
from fuzzywuzzy import process
from datetime import date,datetime

from background_task import background

# API view to search for medicines by name
class MedicineSearchView(APIView):
    """
    API view to search for medicines by name.

    Attributes:
        permission_classes (list): List of permission classes.
            Specifies the permission required to access this view.
            In this case, IsAuthenticated ensures only authenticated users can access the view.
        authentication_classes (list): List of authentication classes.
            Specifies the authentication mechanism used for this view.
            Both DoctorCustomTokenAuthentication and CustomTokenAuthentication are used to authenticate users.

    Methods:
        get(self, request): Handle GET requests for searching medicines by name.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication, CustomTokenAuthentication]

    def get(self, request):
        """
        Handle GET requests for searching medicines by name.

        Args:
            request (HttpRequest): HTTP request object containing query parameter.

        Returns:
            Response: Response object containing serialized medicine data or error message.
        """
        # Extract the query parameter from the request
        query = request.query_params.get('query', '')

        # Check if the query is at least 2 characters long
        if len(query) < 2:
            return Response({'error': 'Query must be at least 2 characters long'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if there's an exact match for the user's query
        exact_match = DrugEye.objects.filter(TradeName__iexact=query).first()
        if exact_match:
            # Serialize the exact match and return the response
            serializer = DrugEyeSerializer(exact_match)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Fetch all drug names from the database
        all_drug_names = DrugEye.objects.values_list('TradeName', flat=True)

        # Perform fuzzy matching to find the closest match to the user's query
        matched_names = process.extract(query, all_drug_names, limit=10)

        # Retrieve drug information for the matched names
        matched_drugs = DrugEye.objects.filter(TradeName__in=[name for name, _ in matched_names])

        # Serialize the matched drugs and return the response
        serializer = DrugEyeSerializer(matched_drugs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# API view to start a session with a user
class StartSessionView(APIView):
    """
    API view to start a session with a user.

    Attributes:
        permission_classes (list): List of permission classes.
            Requires authentication for access.
        authentication_classes (list): List of authentication classes.
            Uses DoctorCustomTokenAuthentication for authentication.
        serializer_class (Serializer): Serializer class for user email.

    Methods:
        post(self, request): Handle POST requests to start a session.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]
    serializer_class = UserSerializerEmail

    def post(self, request):
        """
        Handle POST requests to start a session.

        Args:
            request (HttpRequest): HTTP request object containing user email.

        Returns:
            Response: Response object containing session details or error message.
        """
        # Get the doctor ID from the authenticated user (token)
        doctor_id = request.user.id

        # Serialize the request data
        serializer = self.serializer_class(data=request.data)

        # Check if serializer validation failed
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract user email from validated data
        user_email = serializer.validated_data.get('email')

        # Ensure user_email is not None
        if user_email is None:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user exists
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if there is an active session
        active_sessions = Session.objects.filter(doctor_id=doctor_id)
        if not any(not session.ended for session in active_sessions):
            # Generate OTP
            otp = generate_otp()
            # Create a new session with the doctor's ID and user's ID
            session = Session.objects.create(
                doctor_id=doctor_id,
                user_id=user.id,
                otp=otp
            )
            # Send OTP to user's email
            send_custom_email_otp(user.id, user_email, otp)
            # Return session ID and OTP to the doctor
            return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Session is active'}, status=status.HTTP_400_BAD_REQUEST)

# API view to verify a session
class VerifySessionView(APIView):
    """
    API view to verify a session.

    Attributes:
        permission_classes (list): List of permission classes.
            Requires authentication for access.
        authentication_classes (list): List of authentication classes.
            Uses DoctorCustomTokenAuthentication for authentication.

    Methods:
        post(self, request): Handle POST requests to verify a session.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def post(self, request):
        """
        Handle POST requests to verify a session.

        Args:
            request (HttpRequest): HTTP request object containing OTP.

        Returns:
            Response: Response object containing success message or error message.
        """
        # Get the doctor ID from the authenticated user
        doctor_id = request.user.id

        # Get the most recent session for the doctor
        try:
            session = Session.objects.filter(doctor_id=doctor_id).latest('session_id')
        except Session.DoesNotExist:
            return Response({'error': 'Session not found for this doctor'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the session has expired
        if session.created_at < timezone.now() - timedelta(hours=4):
            # If the session has expired, mark it as ended
            session.ended = True
            session.save()
            return Response({'error': 'Session has expired'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the session is not yet verified
        if not session.verified:
            # Extract OTP from the session
            otp = session.otp

            # Extract OTP from request data
            provided_otp = request.data.get('otp')

            # Check if OTP is provided
            if not provided_otp:
                return Response({'error': 'OTP is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the provided OTP matches the one retrieved
            if int(provided_otp) != int(otp):
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            # Mark the session as verified
            session.verified = True
            session.save()

            # Return success response
            return Response({'message': 'Session verified successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Session already verified'}, status=status.HTTP_400_BAD_REQUEST)

# array of objects
'''{
    "message": "Prescription created successfully",
    "prescription": {
        "doctor_id": 2,
        "user_id": 1,
        "created_at": "2024-02-16T19:25:08.903540",
        "drugs": {
            "BIVATRACIN aerosol powder": {
                "state": "active",
                "start_date": "2024-02-16",
                "end_date": "2024-02-23",
                "quantity": 1,
                "quantity_unit": "aerosol",
                "rate": "20.5",
                "rate_unit": "gram",
                "DrugEye": 23927
            },
            "DERMOTRACIN aerosol powder": {
                "state": "active",
                "start_date": "2024-02-16",
                "end_date": "2024-02-23",
                "quantity": 150,
                "quantity_unit": "aerosol",
                "rate": "23",
                "rate_unit": "ml",
                "DrugEye": 23953
            }
        }
    }
}
'''
# API view to create a prescription by a doctor
class CreatePrescriptionView(APIView):
    """
    View for creating a prescription by a doctor.

    - Requires authentication using DoctorCustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles POST requests to create a prescription.
    - Validates session details, including verification, session expiration, and existence.
    - Automatically populates doctor_id, user_id, and session fields in the prescription data.
    - Fetches scientific name information from DrugEye for each drug in the prescription.
    - Validates prescription data and returns appropriate error messages for validation failures.
    - Saves the prescription if all validation passes and returns success response.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing DoctorCustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def post(self, request):
        """
        POST method to create a prescription.

        - Extracts the doctor ID from the authenticated user.
        - Verifies the session status, ensuring it's verified, not ended, and not expired.
        - Passes the request object to the serializer context.
        - Automatically populates doctor_id, user_id, and session fields in the prescription data.
        - Checks if a prescription already exists for the session.
        - Fetches scientific name information from DrugEye for each drug in the prescription.
        - Creates a prescription serializer with context and modified data.
        - Validates the prescription data and handles date format errors separately.
        - Saves the prescription and returns the success response with the prescription data.

        Returns:
            Response: JSON response containing success or error messages.
        """
        # Extract doctor ID from the authenticated user
        doctor_id = request.user.id

        try:
            # Ensure session is verified and not ended
            session = Session.objects.filter(doctor_id=doctor_id).latest('created_at')
        except Session.DoesNotExist:
            return Response({'error': 'No active session found for this doctor'}, status=status.HTTP_404_NOT_FOUND)

        if not session.verified:
            return Response({'error': 'Session is not verified'}, status=status.HTTP_400_BAD_REQUEST)

        if session.ended:
            return Response({'error': 'Session has ended'}, status=status.HTTP_400_BAD_REQUEST)

        # Check session expiration
        if session.created_at < timezone.now() - timedelta(hours=4):
            session.ended = True
            session.save()
            return Response({'error': 'Session has expired'}, status=status.HTTP_400_BAD_REQUEST)

        # Pass request object to serializer context
        serializer_context = {
            'request': request,
            'session': session
        }

        # Automatically populate doctor_id and user_id
        request.data['doctor_id'] = doctor_id
        request.data['user_id'] = session.user_id
        request.data['session'] = session.session_id

        # Check if a prescription already exists for this session
        prescription = Prescription.objects.filter(doctor_id=doctor_id, user_id=session.user_id, session_id=session.session_id).first()

        if prescription:
            return Response({'error': 'A prescription already exists for this session'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch scientific name from DrugEye and split it into components
        drugs_data = request.data.get('drugs', {})
        for trade_name, drug_data in drugs_data.items():
            try:
                drug_eye = DrugEye.objects.get(TradeName=trade_name)
            except DrugEye.DoesNotExist:
                return Response({'error': f"Drug with trade name '{trade_name}' does not exist."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Add scientific name and its components to the drug data
            drug_data['ScName'] = drug_eye.ScName
            sc_name_components = drug_eye.ScName.split('+')  # Splitting ScName by '+'
            drug_data['ScNameComponents'] = sc_name_components

        # Create prescription serializer with context and modified data
        prescription_serializer = PrescriptionSerializer(data=request.data, context=serializer_context)

        # Validate prescription data
        try:
            prescription_serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            # Check if the error is related to date format
            for field, errors in e.detail.items():
                for error in errors:
                    if 'date' in error.lower() and 'format' in error.lower():
                        return Response({'error': 'Date format is incorrect. Please provide the date in YYYY-MM-DD format.'}, status=status.HTTP_400_BAD_REQUEST)
            # Return other validation errors
            return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)

        # Save prescription
        prescription_serializer.save()
        return Response({'message': 'Prescription created successfully', 'prescription': prescription_serializer.data}, status=status.HTTP_201_CREATED)

# API view to update a prescription by a doctor
class UpdatePrescriptionView(APIView):
    """
    View for updating a prescription by a doctor.

    - Requires authentication using DoctorCustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles PUT requests to update a prescription.
    - Checks if the requesting doctor is authorized to update the prescription.
    - Fetches scientific name information from DrugEye for each drug in the prescription.
    - Validates prescription data and updates the prescription if valid.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing DoctorCustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def put(self, request, prescription_id):
        """
        PUT method to update a prescription.

        Args:
            request (Request): HTTP request object.
            prescription_id (int): ID of the prescription to be updated.

        Returns:
            Response: JSON response containing success or error messages.
        """
        try:
            # Retrieve the prescription object
            prescription = Prescription.objects.get(pk=prescription_id)
        except Prescription.DoesNotExist:
            # Return error response if the prescription does not exist
            return Response({'error': 'Prescription does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the requesting doctor is authorized to update the prescription
        requesting_doctor_id = request.user.id
        if prescription.doctor_id != requesting_doctor_id:
            return Response({'error': 'You are not authorized to update this prescription'}, status=status.HTTP_403_FORBIDDEN)

        # Fetch scientific name from DrugEye and split it into components
        drugs_data = request.data.get('drugs', {})
        for trade_name, drug_data in drugs_data.items():
            try:
                drug_eye = DrugEye.objects.get(TradeName=trade_name)
            except DrugEye.DoesNotExist:
                return Response({'error': f"Drug with trade name '{trade_name}' does not exist."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Add scientific name and its components to the drug data
            drug_data['ScName'] = drug_eye.ScName
            sc_name_components = drug_eye.ScName.split('+')  # Splitting ScName by '+'
            drug_data['ScNameComponents'] = sc_name_components

        # Ensure 'state' field is included in request data
        for trade_name, drug_data in drugs_data.items():
            if 'state' not in drug_data:
                return Response({'error': f"State is required for drug '{trade_name}'"}, status=status.HTTP_400_BAD_REQUEST)

        # Create serializer instance with partial data update
        serializer = PrescriptionSerializer(prescription, data=request.data, partial=True)

        # Validate and save the updated prescription
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Prescription updated successfully', 'prescription': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API view to retrieve details of a prescription    
class PrescriptionDetailView(APIView):
    """
    View for retrieving details of a prescription.

    - Requires authentication using DoctorCustomTokenAuthentication or CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles GET requests to retrieve details of a prescription.
    - Checks if the requesting user is authorized to access the prescription.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing DoctorCustomTokenAuthentication and CustomTokenAuthentication authentication classes.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication, CustomTokenAuthentication]

    def get(self, request, prescription_id):
        """
        GET method to retrieve details of a prescription.

        Args:
            request (Request): HTTP request object.
            prescription_id (int): ID of the prescription to retrieve details for.

        Returns:
            Response: JSON response containing prescription details or error message.
        """
        try:
            # Retrieve the prescription object
            prescription = Prescription.objects.get(id=prescription_id)
        except Prescription.DoesNotExist:
            # Return error response if the prescription does not exist
            return Response({'error': 'Prescription does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        # Extract user and doctor IDs from the prescription
        user_id = prescription.user_id
        doctor_id = prescription.doctor_id

        # Check if the requesting user is authorized to access this prescription
        if not (request.user.id == user_id or request.user.id == doctor_id):
            return Response({'error': 'You are not authorized to access this prescription'}, status=status.HTTP_403_FORBIDDEN)
        
        # Serialize the prescription data and return response
        serializer = PrescriptionSerializer(prescription)
        return Response(serializer.data, status=status.HTTP_200_OK)

# API view to delete a prescription
class DeletePrescriptionView(APIView):
    """
    View for deleting a prescription.

    - Requires authentication using DoctorCustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles DELETE requests to delete a prescription.
    - Checks if the requesting doctor is authorized to delete the prescription.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing DoctorCustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def delete(self, request, prescription_id):
        """
        DELETE method to delete a prescription.

        Args:
            request (Request): HTTP request object.
            prescription_id (int): ID of the prescription to delete.

        Returns:
            Response: JSON response containing success message or error message.
        """
        try:
            # Retrieve the prescription object
            prescription = Prescription.objects.get(pk=prescription_id)
        except Prescription.DoesNotExist:
            # Return error response if the prescription does not exist
            return Response({'error': 'Prescription does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Ensure that the requesting user is the doctor who created the prescription
        requesting_doctor_id = request.user.id
        if prescription.doctor_id != requesting_doctor_id:
            return Response({'error': 'You are not authorized to delete this prescription'}, status=status.HTTP_403_FORBIDDEN)

        # Delete the prescription
        prescription.delete()
        return Response({'message': 'Prescription deleted successfully'}, status=status.HTTP_204_NO_CONTENT) 

"""
Retreive Prescriptions during the session
"""
# API view to retrieve all prescriptions created by a doctor for a specific user during an active session
class DoctorPrescriptionsForUserView(APIView):
    """
    View for retrieving all prescriptions created by a doctor for a specific user during an active session.

    - Requires authentication using DoctorCustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles GET requests to retrieve prescriptions.
    - Retrieves prescriptions created by the doctor for the specified user during an active session.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing DoctorCustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def get(self, request, user_id):
        """
        GET method to retrieve all prescriptions created by a doctor for a specific user during an active session.

        Args:
            request (Request): HTTP request object.
            user_id (int): ID of the user for whom prescriptions are to be retrieved.

        Returns:
            Response: JSON response containing the list of prescriptions or error message.
        """
        # Extract doctor ID from the authenticated user
        doctor_id = request.user.id

        # Ensure session is verified and not ended
        try:
            session = Session.objects.filter(doctor_id=doctor_id).latest('created_at')
        except Session.DoesNotExist:
            return Response({'error': 'No active session found for this doctor'}, status=status.HTTP_404_NOT_FOUND)

        if not session.verified:
            return Response({'error': 'Session is not verified'}, status=status.HTTP_400_BAD_REQUEST)
        if session.ended:
            return Response({'error': 'Session has ended'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve prescriptions created by the doctor for the specified user during the session
        prescriptions = Prescription.objects.filter(doctor_id=doctor_id, user_id=user_id)
        
        # Serialize the prescriptions
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# API view to retrieve prescriptions of a user that a doctor can see during an active session
class UserPrescriptionsView(APIView):
    """
    View for retrieving prescriptions of a user that a doctor can see during an active session.

    - Requires authentication using DoctorCustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles GET requests to retrieve prescriptions.
    - Retrieves prescriptions based on the active session information.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing DoctorCustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def get(self, request):
        """
        GET method to retrieve prescriptions of a user that a doctor can see during an active session.

        Args:
            request (Request): HTTP request object.

        Returns:
            Response: JSON response containing the list of prescriptions or error message.
        """
        # Extract doctor ID from the authenticated user
        doctor_id = request.user.id

        # Ensure session is verified and not ended
        try:
            session = Session.objects.filter(doctor_id=doctor_id).latest('created_at')
        except Session.DoesNotExist:
            return Response({'error': 'No active session found for this doctor'}, status=status.HTTP_404_NOT_FOUND)

        if not session.verified:
            return Response({'error': 'Session is not verified'}, status=status.HTTP_400_BAD_REQUEST)
        if session.ended:
            return Response({'error': 'Session has ended'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve prescriptions based on doctor and session information
        if doctor_id == session.doctor_id:
            # Doctor is the same as the one in the session, retrieve prescriptions by any doctor
            prescriptions = Prescription.objects.filter(user_id=session.user_id)
        else:
            # Doctor is different from the one in the session, return empty queryset
            prescriptions = Prescription.objects.none()

        # Serialize the prescriptions
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# API view to retrieve active prescriptions during an active session for a doctor
class ActivePrescriptionsView(APIView):
    """
    View for retrieving active prescriptions during an active session for a doctor.

    - Requires authentication using DoctorCustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles GET requests to retrieve active prescriptions.
    - Retrieves prescriptions based on the active session information.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing DoctorCustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def get(self, request):
        """
        GET method to retrieve active prescriptions during an active session for a doctor.

        Args:
            request (Request): HTTP request object.

        Returns:
            Response: JSON response containing the list of active prescriptions or error message.
        """
        # Extract doctor ID from the authenticated user
        doctor_id = request.user.id

        # Ensure session is verified and not ended
        try:
            session = Session.objects.filter(doctor_id=doctor_id).latest('created_at')
        except Session.DoesNotExist:
            return Response({'error': 'No active session found for this doctor'}, status=status.HTTP_404_NOT_FOUND)

        if not session.verified:
            return Response({'error': 'Session is not verified'}, status=status.HTTP_400_BAD_REQUEST)

        if session.ended:
            return Response({'error': 'Session has ended'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve prescriptions based on doctor and session information
        if doctor_id == session.doctor_id:
            # Doctor is the same as the one in the session, retrieve prescriptions by any doctor
            prescriptions = Prescription.objects.filter(user_id=session.user_id)
        else:
            # Doctor is different from the one in the session, return empty queryset
            prescriptions = Prescription.objects.none()
        
        # Filter prescriptions to get only active ones
        active_prescriptions = []
        for prescription in prescriptions:
            drugs_data = prescription.drugs  # Assuming prescription.drugs is already a dictionary
            for drug_name, drug_info in drugs_data.items():
                if drug_info['state'] == 'active':
                    active_prescriptions.append(prescription)
                    break  # Break out of the inner loop once an active drug is found

        # Serialize the active prescriptions
        serializer = PrescriptionSerializer(active_prescriptions, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

"""
Doctor
"""
# View for retrieving prescriptions created by a doctor.
class DoctorPrescriptionsView(APIView):
    """
    View for retrieving prescriptions created by a doctor.

    - Requires authentication using DoctorCustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles GET requests to retrieve doctor's prescriptions.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing DoctorCustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def get(self, request):
        """
        GET method to retrieve prescriptions created by a doctor.

        Args:
            request (Request): HTTP request object.

        Returns:
            Response: JSON response containing the list of prescriptions or error message.
        """
        # The doctor ID is extracted from the authenticated user
        doctor_id = request.user.id
        
        # Retrieve prescriptions created by the doctor
        prescriptions = Prescription.objects.filter(doctor_id=doctor_id)
        
        # Serialize the prescriptions
        serializer = PrescriptionSerializer(prescriptions, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
"""
Patient
"""
# View for retrieving prescriptions associated with a patient.
class PatientPrescriptionsView(APIView):
    """
    View for retrieving prescriptions associated with a patient.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles GET requests to retrieve patient's prescriptions.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def get(self, request):
        """
        GET method to retrieve prescriptions associated with a patient.

        Args:
            request (Request): HTTP request object.

        Returns:
            Response: JSON response containing the list of prescriptions or error message.
        """
        # The patient ID is extracted from the authenticated user
        user_id = request.user.id
        
        # Retrieve prescriptions associated with the patient
        prescriptions = Prescription.objects.filter(user_id=user_id)
        
        # Serialize the prescriptions
        serializer = PrescriptionSerializer(prescriptions, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

## Activate APIS
# View for activating drugs in a prescription.
class ActivatePrescriptionView(APIView):
    """
    View for activating drugs in a prescription.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles POST requests to activate drugs in a prescription.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def post(self, request, prescription_id):
        """
        POST method to activate drugs in a prescription.

        Args:
            request (Request): HTTP request object.
            prescription_id (int): ID of the prescription to activate drugs in.

        Returns:
            Response: JSON response containing activation status of drugs or error message.
        """
        # Extract user ID from the authenticated user
        user_id = request.user.id
        
        # Retrieve the prescription from the database
        try:
            prescription = Prescription.objects.get(id=prescription_id, user_id=user_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND) 
        
        # Retrieve drugs data from the prescription
        drugs_data = prescription.drugs
        
        # Initialize lists to keep track of already activated and newly activated drugs
        already_activated_drugs = []
        newly_activated_drugs = []
        
        # Check if any drug in the prescription is already activated
        for drug_name, drug_info in drugs_data.items():
            if drug_info['state'] == 'active':
                already_activated_drugs.append(drug_name)
            else:
                # Activate the drug if it is not already active
                drug_info['state'] = 'active'
                newly_activated_drugs.append(drug_name)
        
        # Save the updated prescription
        prescription.save()
        
        # Prepare response message
        response_data = {}
        if already_activated_drugs:
            response_data['message'] = f"The following drugs are already activated: {', '.join(already_activated_drugs)}"
        if newly_activated_drugs:
            response_data['message'] = response_data.get('message', '') + f"\nActivated the following drugs: {', '.join(newly_activated_drugs)}"
        
        # Return response
        return Response(response_data, status=status.HTTP_200_OK)
    
class ActivateDrugView(APIView):
    """
    View for activating a specific drug in a prescription.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles POST requests to activate a drug in a prescription.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def post(self, request, prescription_id):
        """
        POST method to activate a specific drug in a prescription.

        Args:
            request (Request): HTTP request object.
            prescription_id (int): ID of the prescription containing the drug.

        Returns:
            Response: JSON response containing activation status of the drug or error message.
        """
        # Extract user ID from the authenticated user
        user_id = request.user.id
        
        # Extract drug_name from query parameters
        drug_name = request.query_params.get('drug_name')
        if not drug_name:
            return Response({'error': 'Missing drug_name parameter'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Retrieve the prescription from the database
        prescription = get_object_or_404(Prescription, id=prescription_id, user_id=user_id)
        
        # Retrieve drugs data from the prescription
        drugs_data = prescription.drugs
        
        # Check if the specified drug exists in the prescription
        if drug_name not in drugs_data:
            return Response({'error': 'Drug not found in the prescription'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the specified drug is already activated
        if drugs_data[drug_name]['state'] == 'active':
            return Response({'error': 'Drug is already activated'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Activate the specified drug
        drugs_data[drug_name]['state'] = 'active'
        
        # Save the updated prescription
        prescription.save() 
        
        # Prepare response message
        response_data = {
            'message': f"Drug '{drug_name}' activated successfully"
        }
        
        # Return response
        return Response(response_data, status=status.HTTP_200_OK)
    
## Manual Deactivate APIS
# View for manual Deactivating drugs in a prescription.
class DeActivatePrescriptionView(APIView):
    """
    View for Deactivating drugs in a prescription.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles POST requests to activate drugs in a prescription.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def post(self, request, prescription_id):
        """
        POST method to deactivate drugs in a prescription.

        Args:
            request (Request): HTTP request object.
            prescription_id (int): ID of the prescription to activate drugs in.

        Returns:
            Response: JSON response containing activation status of drugs or error message.
        """
        # Extract user ID from the authenticated user
        user_id = request.user.id
        
        # Retrieve the prescription from the database
        try:
            prescription = Prescription.objects.get(id=prescription_id, user_id=user_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND) 
        
        # Retrieve drugs data from the prescription
        drugs_data = prescription.drugs
        
        # Initialize lists to keep track of already activated and newly activated drugs
        already_deactivated_drugs = []
        newly_deactivated_drugs = []
        
        # Check if any drug in the prescription is already inactive
        for drug_name, drug_info in drugs_data.items():
            if drug_info['state'] == 'inactive':
                already_deactivated_drugs.append(drug_name)
            else:
                # Activate the drug if it is not already inactive
                drug_info['state'] = 'inactive'
                newly_deactivated_drugs.append(drug_name)
        
        # Save the updated prescription
        prescription.save()
        
        # Prepare response message
        response_data = {}
        if already_deactivated_drugs:
            response_data['message'] = f"The following drugs are already deactivated: {', '.join(already_deactivated_drugs)}"
        if newly_deactivated_drugs:
            response_data['message'] = response_data.get('message', '') + f"\nDeactivated the following drugs: {', '.join(newly_deactivated_drugs)}"
        
        # Return response
        return Response(response_data, status=status.HTTP_200_OK)

# View for manual deactivating a specific drug in a prescription.
class DeActivateDrugView(APIView):
    """
    View for manual deactivating a specific drug in a prescription.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles POST requests to deactivate a drug in a prescription.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def post(self, request, prescription_id):
        """
        POST method to deactivate a specific drug in a prescription.

        Args:
            request (Request): HTTP request object.
            prescription_id (int): ID of the prescription containing the drug.

        Returns:
            Response: JSON response containing deactivation status of the drug or error message.
        """
        # Extract user ID from the authenticated user
        user_id = request.user.id
        
        # Extract drug_name from query parameters
        drug_name = request.query_params.get('drug_name')
        if not drug_name:
            return Response({'error': 'Missing drug_name parameter'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Retrieve the prescription from the database
        prescription = get_object_or_404(Prescription, id=prescription_id, user_id=user_id)
        
        # Retrieve drugs data from the prescription
        drugs_data = prescription.drugs
        
        # Check if the specified drug exists in the prescription
        if drug_name not in drugs_data:
            return Response({'error': 'Drug not found in the prescription'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if the specified drug is already deactivated
        if drugs_data[drug_name]['state'] == 'inactive':
            return Response({'error': 'Drug is already deactivated'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Deactivate the specified drug
        drugs_data[drug_name]['state'] = 'inactive'
        
        # Save the updated prescription
        prescription.save() 
        
        # Prepare response message
        response_data = {
            'message': f"Drug '{drug_name}' deactivated successfully"
        }
        
        # Return response
        return Response(response_data, status=status.HTTP_200_OK)
    
##Autmoatic Deactivatin APIS
# View for automatic Deactivating drugs in a prescription.
class AutomaticDeactivateView(APIView):
    """
    View for automatic deactivation of drugs in a prescription based on dates.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles POST requests to automatically deactivate drugs in a prescription.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def post(self, request, prescription_id):
        """
        POST method to automatically deactivate drugs in a prescription based on dates.

        Args:
            request (Request): HTTP request object.
            prescription_id (int): ID of the prescription to automatically deactivate drugs in.

        Returns:
            Response: JSON response containing deactivation status of drugs or error message.
        """
        # Extract user ID from the authenticated user
        user_id = request.user.id
        
        # Retrieve the prescription from the database
        try:
            prescription = Prescription.objects.get(id=prescription_id, user_id=user_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND) 
        
        # Retrieve drugs data from the prescription
        drugs_data = prescription.drugs
        
        # Initialize list to keep track of deactivated drugs
        deactivated_drugs = []
        
        # Check start and end dates of drugs and deactivate if needed
        today = date.today()
        for drug_name, drug_info in drugs_data.items():
            start_date_str = drug_info.get('start_date')
            end_date_str = drug_info.get('end_date')
            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                if start_date <= today <= end_date:
                    # Drug is within its valid period, do nothing
                    pass
                else:
                    # Drug is outside its valid period, deactivate it
                    drug_info['state'] = 'inactive'
                    deactivated_drugs.append(drug_name)
        
        # Save the updated prescription
        prescription.save()
        
        # Prepare response message
        response_data = {}
        if deactivated_drugs:
            response_data['message'] = f"Deactivated the following drugs based on dates: {', '.join(deactivated_drugs)}"
        else:
            response_data['message'] = "No drugs deactivated based on dates"
        
        # Return response
        return Response(response_data, status=status.HTTP_200_OK)

# View for deleting a prescription.
class DeletePrescriptionView(APIView):
    """
    View for deleting a prescription.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles DELETE requests to delete a prescription.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def delete(self, request, prescription_id):
        """
        DELETE method to delete a prescription.

        Args:
            request (Request): HTTP request object.
            prescription_id (int): ID of the prescription to delete.

        Returns:
            Response: JSON response containing success message or error message.
        """
        # Retrieve the prescription from the database
        try:
            prescription = Prescription.objects.get(id=prescription_id, user_id=request.user.id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)

        # Delete the prescription
        prescription.delete()
        
        # Prepare response message
        response_data = {'message': 'Prescription deleted successfully'}

        # Return response
        return Response(response_data, status=status.HTTP_200_OK)

# View to retrieve active,inactive or new prescriptions for a specific user based on the paramater state.
class ActivePrescriptionsForUserView(APIView):
    """
    View to retrieve active،inactive or new prescriptions for a specific user based on the paramater state.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles GET requests to retrieve active prescriptions for the user.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def get(self, request):
        """
        GET method to retrieve active,inactive or new prescriptions for the user.

        Args:
            request (Request): HTTP request object.

        Returns:
            Response: JSON response containing active prescriptions for the user.
        """
        # Obtain the user ID from the authenticated user
        user_id = request.user.id

        # Retrieve the 'state' query parameter from the request, default to 'active' if not provided
        state = request.query_params.get('state', 'active')
        
        # Retrieve all prescriptions for the user
        prescriptions = Prescription.objects.filter(user_id=user_id)

         # Filter prescriptions based on the specified state
        filtered_prescriptions = []
        for prescription in prescriptions:
            drugs_data = prescription.drugs  # Assuming prescription.drugs is already a dictionary
            for drug_name, drug_info in drugs_data.items():
                if drug_info.get('state') == state:
                    filtered_prescriptions.append(prescription)
                    break  # Break out of the inner loop once a prescription is found
        
        # Serialize the filtered prescriptions
        serializer = PrescriptionSerializer(filtered_prescriptions, many=True)

        # Return response with filtered prescriptions
        return Response(serializer.data, status=status.HTTP_200_OK)


## User prescreption doctor info
# View for retrieving Doctor info that create a prescreption associated with a patient.
class PatientPrescriptionsDoctorInfoView(APIView):
    """
    View for retrieving Doctor info that create a prescreption associated with a patient.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def get(self, request):
        user_id = request.user.id
        
        # Retrieve prescriptions associated with the patient
        prescriptions = Prescription.objects.filter(user_id=user_id)
        
        # Serialize the prescriptions
        prescription_serializer = PrescriptionSerializer(prescriptions, many=True)
        
        # Extract doctor information for each prescription
        formatted_data = []
        for prescription_data in prescription_serializer.data:
            prescription_id = prescription_data['id']
            doctor_id = prescription_data.get('doctor_id')
            if doctor_id:
                doctor = Doctor.objects.filter(id=doctor_id).first()
                if doctor:
                    doctor_info = {
                        'id': doctor.id,
                        'fname': doctor.fname,
                        'lname': doctor.lname,
                        'image': doctor.image.url if doctor.image else None
                    }
                    formatted_item = {
                        'id': prescription_id,
                        'doctorInfo': doctor_info,
                        'created_at': prescription_data['created_at']
                    }
                    formatted_data.append(formatted_item)
        
        if formatted_data:
            return Response(formatted_data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No prescriptions found'}, status=status.HTTP_404_NOT_FOUND)
        
# View to retrieve active,inactive or new prescriptions for a specific user based on the paramater state.
class ActivePrescriptionsForUserDoctorinfoView(APIView):
    """
    View to retrieve active,inactive or new prescriptions for a specific user based on the paramater state.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles GET requests to retrieve active prescriptions for the user.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def get(self, request):
        """
        GET method to retrieve active, inactive, or new prescriptions for the user.

        Args:
            request (Request): HTTP request object.

        Returns:
            Response: JSON response containing active, inactive, or new prescriptions for the user.
        """
        # Obtain the user ID from the authenticated user
        user_id = request.user.id

        # Retrieve the 'state' query parameter from the request, default to 'active' if not provided
        state = request.query_params.get('state', 'active')
        
        # Retrieve all prescriptions for the user
        prescriptions = Prescription.objects.filter(user_id=user_id)

        # Filter prescriptions based on the specified state
        filtered_prescriptions = []
        for prescription in prescriptions:
            drugs_data = prescription.drugs  # Assuming prescription.drugs is already a dictionary
            for drug_name, drug_info in drugs_data.items():
                if drug_info.get('state') == state:
                    filtered_prescriptions.append(prescription)
                    break  # Break out of the inner loop once a prescription is found
        
        # Serialize the filtered prescriptions
        prescription_serializer = PrescriptionSerializer(filtered_prescriptions, many=True)
        
        # Extract doctor information for each prescription
        formatted_data = []
        for prescription_data in prescription_serializer.data:
            prescription_id = prescription_data['id']
            doctor_id = prescription_data.get('doctor_id')
            if doctor_id:
                doctor = Doctor.objects.filter(id=doctor_id).first()
                if doctor:
                    doctor_info = {
                        'id': doctor.id,
                        'fname': doctor.fname,
                        'lname': doctor.lname,
                        'image': doctor.image.url if doctor.image else None
                    }
                    formatted_item = {
                        'id': prescription_id,
                        'doctorInfo': doctor_info,
                        'created_at': prescription_data['created_at']
                    }
                    formatted_data.append(formatted_item)
        
        if formatted_data:
            return Response(formatted_data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No prescriptions found'}, status=status.HTTP_404_NOT_FOUND)
    
# Home page api
class HomePageinfoView(APIView):
    """
    View to retrieve active, inactive, or new prescriptions for a specific user based on the parameter state.

    - Requires authentication using CustomTokenAuthentication.
    - Requires the user to be authenticated.
    - Handles GET requests to retrieve active prescriptions for the user.

    Attributes:
        permission_classes (list): List containing IsAuthenticated permission class.
        authentication_classes (list): List containing CustomTokenAuthentication authentication class.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def get(self, request):
        """
        GET method to retrieve active, inactive, or new prescriptions for the user.

        Args:
            request (Request): HTTP request object.

        Returns:
            Response: JSON response containing active, inactive, or new prescriptions for the user.
        """
        # Obtain the user ID from the authenticated user
        user_id = request.user.id
        user_first_name = request.user.fname

        # Retrieve the 'state' query parameter from the URL, default to 'active' if not provided
        state = request.query_params.get('state', 'active')

        # Retrieve all prescriptions for the user
        prescriptions = Prescription.objects.filter(user_id=user_id)

        # Filter prescriptions based on the specified state
        filtered_prescriptions = []
        for prescription in prescriptions:
            drugs_data = prescription.drugs  # Assuming prescription.drugs is already a dictionary
            for drug_name, drug_info in drugs_data.items():
                if drug_info.get('state') == state:
                    filtered_prescriptions.append(prescription)
                    break  # Break out of the inner loop once a prescription is found
        
        # Serialize the filtered prescriptions
        prescription_serializer = PrescriptionSerializer(filtered_prescriptions, many=True)
        
        # Create a dictionary to group user data by user ID
        user_data_dict = {}
        for prescription_data in prescription_serializer.data:
            doctor_id = prescription_data.get('doctor_id')
            if doctor_id:
                doctor = Doctor.objects.filter(id=doctor_id).first()
                if doctor:
                    # Format doctor information
                    doctor_info = {
                        'id': doctor.id,
                        'image': doctor.image.url if doctor.image else None,
                        'username': doctor.username  # Assuming doctor has a username field
                    }

                    # Extract drugs information for the prescription based on state
                    drugs_data = prescription_data['drugs']  # Assuming 'drugs' is already included in prescription_serializer.data
                    drugs_list = []
                    for drug_name, drug_info in drugs_data.items():
                        if drug_info.get('state') == state:
                            drugs_list.append({
                                'commercial_name': drug_name,  # Use the drug name as commercial name
                                'start_date': drug_info.get('start_date'),
                                'end_date': drug_info.get('end_date'),
                                'quantity': drug_info.get('quantity'),
                                'quantity_unit': drug_info.get('quantity_unit')
                            })

                    # Add data to the user data dictionary
                    user_data = user_data_dict.setdefault(user_id, {'first_name': user_first_name, 'doctors': [], 'drugs': []})
                    user_data['doctors'].append(doctor_info)
                    user_data['drugs'].extend(drugs_list)

        # Convert the dictionary values to a list of user data
        formatted_data = list(user_data_dict.values())

        if formatted_data:
            return Response(formatted_data, status=status.HTTP_200_OK)
        else:
            return Response({'message': f'No {state} prescriptions found'}, status=status.HTTP_404_NOT_FOUND)

# end session
class EndSessionView(APIView):
    """
    API view to end a session.

    - Requires authentication using DoctorCustomTokenAuthentication.
    - Handles POST requests to end a session.
    - Clears the session for the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def post(self, request):
        """
        POST method to end a session.

        Args:
            request (Request): HTTP request object.

        Returns:
            Response: JSON response containing success or error messages.
        """
        # Extract doctor ID from the authenticated user
        doctor_id = request.user.id

        # Find the latest session for the doctor
        latest_session = Session.objects.filter(doctor_id=doctor_id).latest('created_at')

        # Check if the latest session is already ended
        if latest_session.ended:
            return Response({'error': 'Session is already ended'}, status=status.HTTP_400_BAD_REQUEST)

        # End the session
        latest_session.ended = True
        latest_session.save()

        return Response({'message': 'Session ended successfully'}, status=status.HTTP_200_OK)
