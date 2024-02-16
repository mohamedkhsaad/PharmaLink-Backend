from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import DrugEye
from .serializers import *
from Doctor.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated

# class MedicineSearchView(APIView):
#     def get(self, request):
#         query = request.query_params.get('query', '')
#         print(query)
#         if len(query) < 2:
#             return Response({'error': 'Query must be at least 2 characters long'}, status=status.HTTP_400_BAD_REQUEST)
#         medicines = DrugEye.objects.filter(trade_name__icontains=str(query))
#         print(medicines)
#         serializer = DrugEyeSerializer(medicines, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
from fuzzywuzzy import process
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import DrugEye
from .serializers import DrugEyeSerializer

class MedicineSearchView(APIView):
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


from .models import *
# from .serializers import PrescriptionSerializer
from .utils import generate_session_id, generate_otp, validate_session, send_otp,send_custom_email_otp



from User.models import User
def get_user_contact_info(user_id):
    try:
        user = User.objects.get(id=user_id)
        # Assuming user has an email field
        return user.email
    except User.DoesNotExist:
        return None

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
        
        # Generate OTP
        otp = generate_otp()
        # Create a new session with the doctor's ID and user's ID
        session = Session.objects.create(
            doctor_id=doctor_id,
            user_id=user.id,
            otp=otp
        )
        send_custom_email_otp(user.id,user_email,otp)
        # Return session ID and OTP to the doctor
        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)

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