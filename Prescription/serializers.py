from rest_framework import serializers
from .models import DrugEye

class DrugEyeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugEye
        fields = '__all__'


class UserIdSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


from User.models import User

class UserSerializerEmail(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['email']



