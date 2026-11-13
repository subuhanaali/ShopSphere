
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )
    def validate_password(self, value):
        user = User(
        username=self.initial_data.get('username', ''),
        email=self.initial_data.get('email', ''),
        first_name=self.initial_data.get('first_name', ''),
        last_name=self.initial_data.get('last_name', '')
    )
        validate_password(value, user=user)
        return value

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'id',
            'user',
            'phone_number',
            'address',
            'city',
            'state',
            'postal_code',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'created_at',
            'updated_at',
        ]
