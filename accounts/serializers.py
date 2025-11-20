from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile
from django.db import transaction


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    matric = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'matric']

    def get_matric(self, obj):
        if obj.role == 'student' and hasattr(obj, 'student_profile'):
            return obj.student_profile.matric_number
        return None

class StudentProfileSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    supervisor_name = serializers.CharField(source='assigned_supervisor.first_name', read_only=True)

    class Meta:
        model = StudentProfile
        fields = ['id', 'user_details', 'matric_number', 'department', 'assigned_supervisor', 'supervisor_name']
        


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    matric_number = serializers.CharField(required=False)
    department = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'role', 'phone_number', 'matric_number', 'department']

    def validate(self, data):
        # If user claims to be a student, matric_number is required
        if data.get('role') == 'student' and not data.get('matric_number'):
            raise serializers.ValidationError({"matric_number": "Matric number is required for students."})
        return data

    def create(self, validated_data):
        # Extract profile data
        matric = validated_data.pop('matric_number', None)
        dept = validated_data.pop('department', None)
        password = validated_data.pop('password')

        # Atomic transaction ensures we don't create a User without a Profile if something fails
        with transaction.atomic():
            user = User.objects.create(**validated_data)
            user.set_password(password) # Hash the password
            user.save()

            if user.role == 'student':
                StudentProfile.objects.create(
                    user=user,
                    matric_number=matric,
                    department=dept
                )
        
        return user