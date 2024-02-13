from rest_framework import serializers
from Doctor.models import*
class Doctorserialzer(serializers.ModelSerializer):
    class Meta:
        model=Doctor
        fields = ['id','fname','lname','username', 'password', 'birthdate', 'email', 'phone', 'gender','license_number','specialization','degree','graduation_date','university']
        extra_kwargs = {'password': {'write_only': True}}
class DoctorAuthTokenSerializer(serializers.Serializer):
    """ 
    Serializer for the user auth Token
    """
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'},
                                     trim_whitespace=False)
    


class DoctorPasswordResetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['email']

class DoctorPasswordUpdateSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance