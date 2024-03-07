# Import necessary modules
from rest_framework import serializers
from User.models import User
from rest_framework import serializers
from .models import *

class DrugEyeSerializer(serializers.ModelSerializer):
    """
    Serializer for the DrugEye model.

    This serializer is used to convert DrugEye model instances into JSON representations,
    making them suitable for transmission over HTTP as responses from API endpoints.

    Attributes:
        model (class): The DrugEye model class to be serialized.
        fields (list or tuple): Specifies the fields to include in the serialized output.
            Using '__all__' includes all fields from the model.
    """
    class Meta:
        model = DrugEye
        fields = '__all__'

class UserIdSerializer(serializers.Serializer):
    """
    Serializer for validating user ID.

    This serializer is used to validate user IDs provided in API requests.

    Attributes:
        user_id (IntegerField): Field for user ID, expected to be an integer.
    """
    user_id = serializers.IntegerField()

class UserSerializerEmail(serializers.ModelSerializer):
    """
    Serializer for user email.

    This serializer is used to serialize and validate user email fields.

    Attributes:
        email (EmailField): Field for user email, expected to be in a valid email format.
    """
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['email']

class PrescriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for Prescription model.

    This serializer is used to serialize and validate prescription data before saving it to the database.

    Attributes:
        DATE_FORMAT (str): Expected date format for start_date and end_date fields.

    Methods:
        validate_drugs(self, drugs): Validate drugs data and link them with DrugEye model.
        create(self, validated_data): Create a new prescription instance with validated data.
    """

    DATE_FORMAT = '%Y-%m-%d'  # Specify the expected date format

    def validate_drugs(self, drugs):
        """
        Validate drugs data and link them with DrugEye model.

        Args:
            drugs (dict): Dictionary containing drug data with trade names as keys.

        Returns:
            dict: Validated drugs data with DrugEye IDs added.

        Raises:
            serializers.ValidationError: If any drug data fails validation.
        """
        for trade_name, drug_data in drugs.items():
            try:
                # Fetch the DrugEye instance based on the trade name
                drug_eye = DrugEye.objects.get(TradeName=trade_name)
            except DrugEye.DoesNotExist:
                raise serializers.ValidationError(f"Drug with trade name '{trade_name}' does not exist.")

            # Validate drug data fields
            state = drug_data.get('state', 'new')
            if state not in ['active', 'inactive', 'new']:
                raise serializers.ValidationError(f"Invalid state '{state}' for drug '{trade_name}'.")

            start_date = drug_data.get('start_date')
            if start_date:
                try:
                    timezone.datetime.strptime(start_date, self.DATE_FORMAT)
                except ValueError:
                    raise serializers.ValidationError(f"Invalid date format for drug '{trade_name}'. Date should be in format '{self.DATE_FORMAT}'.")

            end_date = drug_data.get('end_date')
            if start_date and end_date:
                start_date_obj = timezone.datetime.strptime(start_date, self.DATE_FORMAT).date()
                end_date_obj = timezone.datetime.strptime(end_date, self.DATE_FORMAT).date()
                if start_date_obj > end_date_obj:
                    raise serializers.ValidationError(f"End date must be after or equal to start date for drug '{trade_name}'.")
                if start_date_obj < timezone.now().date():
                    raise serializers.ValidationError(f"Start date must be in the future for drug '{trade_name}'.")

            quantity = drug_data.get('quantity')
            if not isinstance(quantity, int) or quantity <= 0:
                raise serializers.ValidationError(f"Invalid quantity '{quantity}' for drug '{trade_name}'.")

            quantity_unit = drug_data.get('quantity_unit')
            if not isinstance(quantity_unit, str) or not quantity_unit:
                raise serializers.ValidationError(f"Invalid quantity unit '{quantity_unit}' for drug '{trade_name}'.")

            rate = drug_data.get('rate')
            if not isinstance(rate, float) or rate <= 0:
                raise serializers.ValidationError(f"Invalid rate '{rate}' for drug '{trade_name}'.")

            rate_unit = drug_data.get('rate_unit')
            if not isinstance(rate_unit, str) or not rate_unit:
                raise serializers.ValidationError(f"Invalid rate unit '{rate_unit}' for drug '{trade_name}'.")

            # Add drug_eye ID to the drug_data
            drug_data['DrugEye'] = drug_eye.ID
        return drugs

    def create(self, validated_data):
        """
        Create a new prescription instance with validated data.

        Args:
            validated_data (dict): Validated data for creating the prescription.

        Returns:
            Prescription: Newly created prescription instance.
        """
        session = self.context.get('session')
        validated_data['doctor_id'] = self.context['request'].user.id
        validated_data['user_id'] = session.user_id
        validated_data['session'] = session
        validated_data['created_at'] = timezone.now()  # Ensure created_at is set

        drugs = validated_data.get('drugs')
        for trade_name, drug_data in drugs.items():
            start_date = drug_data.get('start_date')
            if start_date:
                try:
                    timezone.datetime.strptime(start_date, self.DATE_FORMAT)
                except ValueError:
                    raise serializers.ValidationError(f"Invalid date format for drug '{trade_name}'. Date should be in format '{self.DATE_FORMAT}'.")

        # Set the state to 'new' automatically
        validated_data['drugs'] = {
            trade_name: {**drug_data, 'state': 'new'}
            for trade_name, drug_data in drugs.items()
        }

        return super().create(validated_data)

    class Meta:
        model = Prescription
        fields = ['id', 'doctor_id', 'user_id', 'created_at', 'drugs']