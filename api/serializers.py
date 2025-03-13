from django.contrib.auth.models import User
from rest_framework import serializers

from api.models import StoryJob

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        email = validated_data['email']
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email address is already in use."})
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

class StoryJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryJob
        fields = ['id', 'title', 'description', 'status', 'position', 'created_at', 'updated_at']
        read_only_fields = ['status', 'position', 'created_at', 'updated_at']