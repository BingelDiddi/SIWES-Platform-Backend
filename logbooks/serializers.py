from rest_framework import serializers
from .models import LogEntry, FinalReport

class LogEntrySerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    matric = serializers.CharField(source='student.student_profile.matric_number', read_only=True)
    class Meta:
        model = LogEntry
        fields = ['id', 'date', 'time_in', 'time_out', 'activities', 'status', 'supervisor_feedback', 'student_name', 'matric']
        read_only_fields = ['status', 'supervisor_feedback'] # Students can't edit status
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

class LogReviewSerializer(serializers.ModelSerializer):
    # Serializer specifically for Supervisors to approve/reject
    class Meta:
        model = LogEntry
        fields = ['status', 'supervisor_feedback']

class FinalReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinalReport
        fields = ['id', 'title', 'file', 'uploaded_at']