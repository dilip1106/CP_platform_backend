from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # use Django default `id`
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'country',
            'rating',
            'is_admin',
        ]
        read_only_fields = [
            'id',
            'rating',
            'is_admin',
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'full_name',
            'country',
        ]

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name'),
            country=validated_data.get('country'),
        )
