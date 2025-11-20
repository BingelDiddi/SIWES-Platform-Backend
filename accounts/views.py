from rest_framework import viewsets, permissions, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import StudentProfile
from .serializers import UserSerializer, StudentProfileSerializer, RegistrationSerializer
from rest_framework.permissions import AllowAny

User = get_user_model()

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {}
        
        if user.role == 'admin':
            data['total_students'] = User.objects.filter(role='student').count()
            data['total_supervisors'] = User.objects.filter(role='supervisor').count()
        
        elif user.role == 'supervisor':
            my_students = StudentProfile.objects.filter(assigned_supervisor=user)
            data['student_count'] = my_students.count()
            # Add logic for pending reviews count here
        
        return Response(data)

class AdminStudentViewSet(viewsets.ModelViewSet):
    # Admin only: Manage students and assign supervisors
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny] # Allow anyone to register
    serializer_class = RegistrationSerializer
    

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role
        }
        if user.role == 'student' and hasattr(user, 'student_profile'):
            data['matric'] = user.student_profile.matric_number
        return Response(data)


class SupervisorListView(generics.ListAPIView):
    queryset = User.objects.filter(role='supervisor')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]