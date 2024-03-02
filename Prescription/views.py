from django.shortcuts import render
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import DrugEye
from .serializers import UserSerializerEmail
from Doctor.authentication import DoctorCustomTokenAuthentication
from User.authentication import CustomTokenAuthentication
from .serializers import DrugEyeSerializer
from .models import *
from .utils import generate_session_id, generate_otp, validate_session, send_otp,send_custom_email_otp
from User.models import User
from django.utils import timezone
from datetime import timedelta
from .serializers import PrescriptionSerializer
from rest_framework.permissions import IsAuthenticated
from fuzzywuzzy import process
import json
from rest_framework.exceptions import ValidationError

class MedicineSearchView(APIView):
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [DoctorCustomTokenAuthentication]
    def get(self, request):
        query = request.query_params.get('query', '')
        if len(query) < 2:
            return Response({'error': 'Query must be at least 2 characters long'}, status=status.HTTP_400_BAD_REQUEST)
        # Check if there's an exact match for the user's query
        exact_match = DrugEye.objects.filter(TradeName__iexact=query).first()
        if exact_match:
            serializer = DrugEyeSerializer(exact_match)
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Fetch all drug names from the database
        all_drug_names = DrugEye.objects.values_list('TradeName', flat=True)
        # Perform fuzzy matching to find the closest match to the user's query
        matched_names = process.extract(query, all_drug_names, limit=10)
        # Retrieve drug information for the matched names
        matched_drugs = DrugEye.objects.filter(TradeName__in=[name for name, _ in matched_names])
        # Serialize the matched drugs
        serializer = DrugEyeSerializer(matched_drugs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StartSessionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]
    serializer_class = UserSerializerEmail
    def post(self, request):
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
            send_custom_email_otp(user.id, user_email, otp)
            # Return session ID and OTP to the doctor
            return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Session is active'}, status=status.HTTP_400_BAD_REQUEST)

class VerifySessionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]
    def post(self, request):
        # Get the doctor ID from the authenticated user
        doctor_id = request.user.id
        # Get the most recent session for the doctor
        try:
            session = Session.objects.filter(doctor_id=doctor_id).latest('session_id')
        except Session.DoesNotExist:
            return Response({'error': 'Session not found for this doctor'}, status=status.HTTP_404_NOT_FOUND)
        if session.created_at < timezone.now() - timedelta(hours=4):
            # If the session has expired, mark it as ended
            session.ended = True
            session.save()
            return Response({'error': 'Session has expired'}, status=status.HTTP_400_BAD_REQUEST)
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

class CreatePrescriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def post(self, request):
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
    
class UpdatePrescriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]

    def put(self, request, prescription_id):
        try:
            prescription = Prescription.objects.get(pk=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the requesting doctor is the same as the one who created the prescription
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

        serializer = PrescriptionSerializer(prescription, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Prescription updated successfully', 'prescription': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
     
class PrescriptionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]
    def get(self, request, prescription_id):
        try:
            prescription = Prescription.objects.get(id=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription does not exist'}, status=status.HTTP_404_NOT_FOUND)
        # Check if the requesting doctor is authorized to access this prescription
        requesting_doctor_id = request.user.id
        if prescription.doctor_id != requesting_doctor_id:
            return Response({'error': 'You are not authorized to access this prescription'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PrescriptionSerializer(prescription)
        return Response(serializer.data, status=status.HTTP_200_OK)
     
class DeletePrescriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]
    def delete(self, request, prescription_id):
        try:
            prescription = Prescription.objects.get(pk=prescription_id)
        except Prescription.DoesNotExist:
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
# all Doctor prescreptions that he prescriped for the patient in the session, could see during the session only
class DoctorPrescriptionsForUserView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]
    def get(self, request, user_id):
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

        # Retrieve prescriptions created by the doctor for the specified user
        prescriptions = Prescription.objects.filter(doctor_id=doctor_id, user_id=user_id)
        
        # Serialize the prescriptions
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK) 
# all user prescreptions that the doctor could see during the session only
class UserPrescriptionsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]
    def get(self, request):
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
    
class ActivePrescriptionsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]
    def get(self, request):
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
            print(prescriptions)
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
class DoctorPrescriptionsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [DoctorCustomTokenAuthentication]
    def get(self, request):
        # The doctor ID is extracted from the authenticated user
        doctor_id = request.user.id
        # Retrieve prescriptions created by the doctor for the specified user
        prescriptions = Prescription.objects.filter(doctor_id=doctor_id)
        # Serialize the prescriptions
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
"""
Patient
"""
class PatientPrescriptionsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]
    def get(self, request):
        # The doctor ID is extracted from the authenticated user
        user_id = request.user.id
        # Retrieve prescriptions created by the doctor for the specified user
        prescriptions = Prescription.objects.filter(user_id=user_id)
        # Serialize the prescriptions
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ActivatePrescriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]
    def post(self, request, prescription_id):
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
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def post(self, request, prescription_id, drug_name):
        # Extract user ID from the authenticated user
        user_id = request.user.id
        # Retrieve the prescription from the database
        try:
            prescription = Prescription.objects.get(id=prescription_id, user_id=user_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)
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

class DeletePrescriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def delete(self, request, prescription_id):
        # Retrieve the prescription from the database
        try:
            prescription = Prescription.objects.get(id=prescription_id, user_id=request.user.id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)

        # Delete the prescription
        prescription.delete()
        return Response({'message': 'Prescription deleted successfully'}, status=status.HTTP_200_OK)
    
class ActivePrescriptionsForUserView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]
    def get(self, request):
        # Obtain the user ID from the authenticated user
        user_id = request.user.id
        # Retrieve all prescriptions for the user
        prescriptions = Prescription.objects.filter(user_id=user_id)
        # Filter prescriptions to get only active ones
        active_prescriptions = []
        for prescription in prescriptions:
            drugs_data = prescription.drugs  # Assuming prescription.drugs is already a dictionary
            for drug_name, drug_info in drugs_data.items():
                if drug_info.get('state') == 'active':  # Ensure 'state' key exists and its value is 'active'
                    active_prescriptions.append(prescription)
                    break  # Break out of the inner loop once an active drug is found
        
        # Serialize the active prescriptions
        serializer = PrescriptionSerializer(active_prescriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)