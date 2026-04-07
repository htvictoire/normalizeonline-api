
from apps.accounts.models import GuestUser, User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import User


class GuestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestUser
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):

    def validate_password(self, value):
        validate_password(value)
        return value
    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]
        extra_kwargs = {
            "password": {"write_only": True},
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)