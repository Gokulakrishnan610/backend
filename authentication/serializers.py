from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    # year = serializers.CharField(required=True)
    # dept = serializers.CharField(required=True)
    gender = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'gender')


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password',)