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

# class DrugSerializer(serializers.Serializer):
#     # drug_id = serializers.IntegerField()
#     state = serializers.ChoiceField(choices=Drug.STATE_CHOICES)
#     start_date = serializers.DateField()
#     end_date = serializers.DateField()
#     quantity = serializers.IntegerField()
#     quantity_unit = serializers.CharField(max_length=100)
#     rate = serializers.DecimalField(max_digits=10, decimal_places=2)
#     rate_unit = serializers.CharField(max_length=100)
#     TradeName = serializers.CharField(max_length=255)

class PrescriptionSerializer(serializers.ModelSerializer):
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
            state = drug_data.get('state')
            if state not in ['active', 'inactive', 'new']:
                raise serializers.ValidationError(f"Invalid state '{state}' for drug '{trade_name}'.")

            start_date = drug_data.get('start_date')
            end_date = drug_data.get('end_date')
            if start_date and end_date and start_date > end_date:
                raise serializers.ValidationError(f"End date must be after start date for drug '{trade_name}'.")

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
        return super().create(validated_data)
    class Meta:
        model = Prescription
        fields = ['id', 'doctor_id', 'user_id', 'created_at', 'drugs']
