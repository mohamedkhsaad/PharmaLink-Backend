from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import DrugEye
from .serializers import UserSerializerEmail
from Doctor.authentication import CustomTokenAuthentication
from .serializers import DrugEyeSerializer
from .models import *
from .utils import generate_session_id, generate_otp, validate_session, send_otp,send_custom_email_otp
from User.models import User
from django.utils import timezone
from datetime import timedelta
from .serializers import PrescriptionSerializer
from rest_framework.permissions import IsAuthenticated
from fuzzywuzzy import process

class MedicineSearchView(APIView):
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [CustomTokenAuthentication]
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
    authentication_classes = [CustomTokenAuthentication]
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
    authentication_classes = [CustomTokenAuthentication]
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
}'''

class CreatePrescriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

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
        request.data['session']=session.session_id

        # Check if a prescription already exists for this session
        prescription = Prescription.objects.filter(doctor_id=doctor_id, user_id=session.user_id, session_id=session.session_id).first()

        if prescription:
            return Response({'error': 'A prescription already exists for this session'}, status=status.HTTP_400_BAD_REQUEST)

        # Create prescription serializer with context
        prescription_serializer = PrescriptionSerializer(data=request.data, context=serializer_context)

        # Check if the session has ended
        if session.ended:
            pass
            # return Response({'error': 'Session has ended'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate prescription data
        if prescription_serializer.is_valid():
            # Save prescription
            prescription_serializer.save()
            return Response({'message': 'Prescription created successfully', 'prescription': prescription_serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(prescription_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
