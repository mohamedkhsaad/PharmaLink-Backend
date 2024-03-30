"""
This file contains API views for handling drug interaction checks and related functionalities.
It includes views for checking drug interactions in a prescription, based on trade names of drugs,
among all active prescriptions for a user, and for all user prescriptions. 
These views are designed to provide information about potential drug interactions, if any are found,
while ensuring proper authentication and authorization for patients and doctors.
"""

# Import necessary modules and classes
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import DDIInteraction
from Prescription.models import Prescription ,DrugEye
from User.authentication import CustomTokenAuthentication
from Doctor.authentication import DoctorCustomTokenAuthentication
from Prescription.models import Session
from datetime import timedelta
from django.utils import timezone

# Patient and Doctor Prescription Drug Interaction
# View class for checking drug interactions in a prescription
class DrugInteractionCheckView(APIView):
    """
    API view to check for drug interactions in a prescription.

    - Inherits from APIView provided by Django REST Framework.
    - Requires authentication using custom tokens for both patients and doctors.
    - Requires the requesting user to be authenticated.
    """

    authentication_classes = [CustomTokenAuthentication, DoctorCustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, prescription_id):
        """
        Handles POST requests to check for drug interactions in a prescription.

        Parameters:
            - request (HttpRequest): The request object.
            - prescription_id (int): The ID of the prescription to check for interactions.

        Returns:
            - Response: A response containing information about drug interactions, if any are found.
        """

        try:
            # Get the prescription from the database using the provided ID
            prescription = Prescription.objects.get(id=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'error': 'Prescription not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Extract user and doctor IDs from the prescription
        user_id = prescription.user_id
        doctor_id = prescription.doctor_id

        # Check if the requesting user is authorized to access this prescription
        if not (request.user.id == user_id or request.user.id == doctor_id):
            return Response({'error': 'You are not authorized to access this prescription'}, status=status.HTTP_403_FORBIDDEN)
        
        # Extract drugs data from the prescription
        drugs_data = prescription.drugs

        # List to store interactions found
        interactions = []

        # Iterate through each pair of drugs and check for interactions
        for drug_name1, drug_data1 in drugs_data.items():
            for drug_name2, drug_data2 in drugs_data.items():
                if drug_name1 != drug_name2:
                    # Get ScNameComponents for each drug and convert to lowercase for case-insensitive comparison
                    components1 = [component.lower() for component in drug_data1.get('ScNameComponents', [])]
                    components2 = [component.lower() for component in drug_data2.get('ScNameComponents', [])]
                    
                    # Check for interactions between ScNameComponents of the two drugs
                    for component1 in components1:
                        for component2 in components2:
                            # Check for interactions in both directions
                            interaction = self.check_interaction(component1, component2)
                            if interaction:
                                interactions.append({
                                    'drug1': drug_name1,
                                    'drug2': drug_name2,
                                    'interaction_type': interaction
                                })

        # Return interactions found
        if interactions:
            return Response(interactions, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No interactions found'}, status=status.HTTP_200_OK)

    def check_interaction(self, component1, component2):
        """
        Method to check for drug interactions between two drug components.

        Parameters:
            - component1 (str): The first drug component to check.
            - component2 (str): The second drug component to check.

        Returns:
            - str: The type of interaction found, if any.
        """

        # Check if there's an interaction between component1 and component2 in the DDI database
        interactions = DDIInteraction.objects.filter(
            drug1_name__iexact=component1,
            drug2_name__iexact=component2
        )
        interaction_types = [interaction.interaction_type for interaction in interactions]
        return interaction_types
    
# View class for checking drug interactions by trade name
class DrugInteractionByTradeNameView(APIView):
    """
    API view to check for drug interactions based on trade names of drugs.

    - Inherits from APIView provided by Django REST Framework.
    - Requires authentication using custom tokens for both patients and doctors.
    - Requires the requesting user to be authenticated.
    """

    authentication_classes = [CustomTokenAuthentication, DoctorCustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handles POST requests to check for drug interactions based on trade names of drugs.

        Parameters:
            - request (HttpRequest): The request object.

        Returns:
            - Response: A response containing information about drug interactions, if any are found.
        """

        # Get the trade names of the two drugs from the request data
        trade_name1 = request.data.get('trade_name1', '').strip()
        trade_name2 = request.data.get('trade_name2', '').strip()

        # Check if both trade names are provided
        if not trade_name1 or not trade_name2:
            return Response({'error': 'Trade names of both drugs are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch scientific names and their components from DrugEye for the given trade names
        drug1_info = self.get_drug_info(trade_name1)
        drug2_info = self.get_drug_info(trade_name2)

        # Check if both drugs are found in DrugEye
        if not drug1_info or not drug2_info:
            return Response({'error': 'One or both drugs not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if there's an interaction between the two drugs based on their components
        interaction_types = self.check_interaction(drug1_info['ScNameComponents'], drug2_info['ScNameComponents'])

        # Return interactions found
        if interaction_types:
            return Response({'Type':'Risky','interaction_types': interaction_types}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No interaction found'}, status=status.HTTP_200_OK)

    def get_drug_info(self, trade_name):
        """
        Helper method to fetch drug information from DrugEye based on trade name.

        Parameters:
            - trade_name (str): The trade name of the drug.

        Returns:
            - dict or None: A dictionary containing drug information if found, else None.
        """

        try:
            drug_eye = DrugEye.objects.get(TradeName=trade_name)
        except DrugEye.DoesNotExist:
            return None
        # Convert ScNameComponents to lowercase for case-insensitive comparison
        sc_name_components_lower = [component.lower() for component in drug_eye.ScName.split('+')]
        print(sc_name_components_lower)
        return {
            'ScName': drug_eye.ScName,
            'ScNameComponents': sc_name_components_lower
        }

    def check_interaction(self, components1, components2):
        """
        Helper method to check for drug interactions between components of two drugs.

        Parameters:
            - components1 (list): A list of components of the first drug.
            - components2 (list): A list of components of the second drug.

        Returns:
            - list: A list of interaction types found between the two drugs' components.
        """

        # Check if there's an interaction between the components of the two drugs in the DDI database
        interactions = []
        for component1 in components1:
            for component2 in components2:
                interactions += self.get_interactions(component1, component2)
        return interactions

    def get_interactions(self, component1, component2):
        """
        Helper method to retrieve interactions between two components from the DDI database.

        Parameters:
            - component1 (str): The first drug component.
            - component2 (str): The second drug component.

        Returns:
            - list: A list of interaction types found between the two components.
        """

        interactions = DDIInteraction.objects.filter(
            drug1_name__icontains=component1,
            drug2_name__icontains=component2
        ).values_list('interaction_type', flat=True)

        return list(interactions)

# During the session
# View class for checking drug interactions among all user prescriptions
class DrugInteractionCheckViewForAllUserPrescriptions(APIView):
    """
    API view to check for drug interactions among all active prescriptions for a user.

    - Inherits from APIView provided by Django REST Framework.
    - Requires authentication using custom tokens for doctors.
    - Requires the requesting user to be authenticated.
    """

    authentication_classes = [DoctorCustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handles POST requests to check for drug interactions among all active prescriptions for a user.

        Parameters:
            - request (HttpRequest): The request object.

        Returns:
            - Response: A response containing information about drug interactions, if any are found.
        """

        # Extract doctor ID from the authenticated user
        doctor_id = request.user.id
        
        # Step 1: Ensure session is verified and not ended
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

        # Step 2: Retrieve active prescriptions for the user
        user_id = session.user_id
        
        # Retrieve all prescriptions for the user
        prescriptions = Prescription.objects.filter(user_id=user_id)
        active_prescriptions = []

        # Add prescription from the session to active prescriptions
        session_prescription = Prescription.objects.filter(doctor_id=doctor_id, user_id=user_id, session_id=session.session_id).first()
        if session_prescription:
            active_prescriptions.append(session_prescription)

        for prescription in prescriptions:
            drugs_data = prescription.drugs  # Assuming prescription.drugs is already a dictionary
            for drug_name, drug_info in drugs_data.items():
                if drug_info.get('state') in ['active', 'new']:  # Ensure 'state' key exists and its value is 'active' or 'new'
                    active_prescriptions.append(prescription)
                    break  # Break out of the inner loop once an active drug is found

        # List to store interactions found
        interactions = []

        # Step 3: Check for interactions between all the drugs of these prescriptions
        for prescription1 in active_prescriptions:
            drugs_data1 = prescription1.drugs
            for prescription2 in active_prescriptions:
                drugs_data2 = prescription2.drugs
                for drug_name1, drug_data1 in drugs_data1.items():
                    for drug_name2, drug_data2 in drugs_data2.items():
                        if drug_name1 != drug_name2:
                            components1 = [component.lower() for component in drug_data1.get('ScNameComponents', [])]
                            components2 = [component.lower() for component in drug_data2.get('ScNameComponents', [])]
                            for component1 in components1:
                                for component2 in components2:
                                    interaction = self.check_interaction(component1, component2)
                                    if interaction:
                                        interactions.append({
                                            'prescription_id_1': prescription1.id,
                                            'prescription_id_2': prescription2.id,
                                            'drug1': drug_name1,
                                            'drug2': drug_name2,
                                            'scname1': drug_data1.get('ScName'),
                                            'scname2': drug_data2.get('ScName'),
                                            'state1': drug_data1.get('state'),
                                            'state2': drug_data2.get('state'),
                                            'interaction_type': interaction
                                        })

        # Return interactions found
        if interactions:
            return Response(interactions, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No interactions found'}, status=status.HTTP_200_OK)

    def check_interaction(self, component1, component2):
        """
        Helper method to check for interactions between two drug components.

        Parameters:
            - component1 (str): The first drug component.
            - component2 (str): The second drug component.

        Returns:
            - list: A list of interaction types found between the two components.
        """

        # Step 4: Check for interactions between component1 and component2
        interactions = DDIInteraction.objects.filter(
            drug1_name__iexact=component1,
            drug2_name__iexact=component2
        )
        interaction_types = [interaction.interaction_type for interaction in interactions]
        return interaction_types

# for patient all prescreptions check
# View class for checking drug interactions among all active prescriptions for a user
class DrugInteractionCheckViewForUser(APIView):
    """
    API view to check for drug interactions among all active prescriptions for a specific user.

    - Inherits from APIView provided by Django REST Framework.
    - Requires authentication using custom tokens for patients.
    - Requires the requesting user to be authenticated.
    """

    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handles POST requests to check for drug interactions among all active prescriptions for a specific user.

        Parameters:
            - request (HttpRequest): The request object.

        Returns:
            - Response: A response containing information about drug interactions, if any are found.
        """

        # Extract user ID from the authenticated user
        user_id = request.user.id

        # Extract the target user ID if specified in the request data
        target_user_id = request.data.get('target_user_id')

        # If target_user_id is provided, ensure it matches the requesting user's ID
        if target_user_id and target_user_id != user_id:
            return Response({'error': 'You are not authorized to check prescriptions for another user'}, status=status.HTTP_403_FORBIDDEN)

        # Determine the user ID to use for querying prescriptions
        query_user_id = target_user_id if target_user_id else user_id

        # Retrieve all prescriptions for the user
        prescriptions = Prescription.objects.filter(user_id=query_user_id)
        active_prescriptions = []

        for prescription in prescriptions:
            drugs_data = prescription.drugs  # Assuming prescription.drugs is already a dictionary
            for drug_name, drug_info in drugs_data.items():
                if drug_info.get('state') in ['active', 'new']:  # Ensure 'state' key exists and its value is 'active' or 'new'
                    active_prescriptions.append(prescription)
                    break  # Break out of the inner loop once an active drug is found

        # List to store interactions found
        interactions = []

        # Step 3: Check for interactions between all the drugs of these prescriptions
        for prescription1 in active_prescriptions:
            drugs_data1 = prescription1.drugs
            for prescription2 in active_prescriptions:
                drugs_data2 = prescription2.drugs
                for drug_name1, drug_data1 in drugs_data1.items():
                    for drug_name2, drug_data2 in drugs_data2.items():
                        if drug_name1 != drug_name2:
                            components1 = [component.lower() for component in drug_data1.get('ScNameComponents', [])]
                            components2 = [component.lower() for component in drug_data2.get('ScNameComponents', [])]
                            for component1 in components1:
                                for component2 in components2:
                                    interaction = self.check_interaction(component1, component2)
                                    if interaction:
                                        interactions.append({
                                            'prescription_id_1': prescription1.id,
                                            'prescription_id_2': prescription2.id,
                                            'drug1': drug_name1,
                                            'drug2': drug_name2,
                                            'scname1': drug_data1.get('ScName'),
                                            'scname2': drug_data2.get('ScName'),
                                            'state1': drug_data1.get('state'),
                                            'state2': drug_data2.get('state'),
                                            'interaction_type': interaction
                                        })

        # Return interactions found
        if interactions:
            return Response(interactions, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No interactions found'}, status=status.HTTP_200_OK)

    def check_interaction(self, component1, component2):
        """
        Helper method to check for interactions between two drug components.

        Parameters:
            - component1 (str): The first drug component.
            - component2 (str): The second drug component.

        Returns:
            - list: A list of interaction types found between the two components.
        """

        # Step 4: Check for interactions between component1 and component2
        interactions = DDIInteraction.objects.filter(
            drug1_name__iexact=component1,
            drug2_name__iexact=component2
        )
        interaction_types = [interaction.interaction_type for interaction in interactions]
        return interaction_types