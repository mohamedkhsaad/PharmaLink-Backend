from rest_framework import serializers
from User.models import User
from rest_framework import serializers
from .models import *

class DrugEyeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugEye
        fields = '__all__'

class UserIdSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

class UserSerializerEmail(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['email']

class PrescriptionSerializer(serializers.ModelSerializer):
    DATE_FORMAT = '%Y-%m-%d'  # Specify the expected date format

    def validate_drugs(self, drugs):
        """
        Validate drugs data and link them with DrugEye model
        """
        for trade_name, drug_data in drugs.items():
            try:
                drug_eye = DrugEye.objects.get(TradeName=trade_name)
            except DrugEye.DoesNotExist:
                raise serializers.ValidationError(f"Drug with trade name '{trade_name}' does not exist.")

            # Validate the drug data fields
            state = drug_data.get('state', 'new')  # Set default state to 'new' if not provided
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
                start_date_obj = timezone.datetime.strptime(start_date, self.DATE_FORMAT).date()  # Convert to datetime.date
                end_date_obj = timezone.datetime.strptime(end_date, self.DATE_FORMAT).date()  # Convert to datetime.date
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