from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import LogEntry, FinalReport
from .serializers import LogEntrySerializer, LogReviewSerializer, FinalReportSerializer

class LogBookViewSet(viewsets.ModelViewSet):
    serializer_class = LogEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return LogEntry.objects.filter(student=user)
        elif user.role == 'supervisor':
            # Fix for Duplicates: Add .distinct() to ensure unique logs
            return LogEntry.objects.filter(
                student__student_profile__assigned_supervisor=user
            ).distinct()
        return LogEntry.objects.none()

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    # === NEW: Logic to reset status on edit ===
    def perform_update(self, serializer):
        # If a student is editing, force status back to 'pending'
        if self.request.user.role == 'student':
            serializer.save(status='pending')
        else:
            serializer.save()

    # Supervisor Review Action
    @action(detail=True, methods=['post'], url_path='review')
    def review_log(self, request, pk=None):
        log = self.get_object()
        # Ensure only supervisor can review
        if request.user.role != 'supervisor':
            return Response({"error": "Only supervisors can review"}, status=403)
        
        serializer = LogReviewSerializer(log, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class ReportViewSet(viewsets.ModelViewSet):
    queryset = FinalReport.objects.all()
    serializer_class = FinalReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)