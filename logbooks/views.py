from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import LogEntry, FinalReport
from .serializers import LogEntrySerializer, LogReviewSerializer, FinalReportSerializer
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

User = get_user_model()

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
        
        
class GeneratePDFReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        # 1. Validation & Setup
        if request.user.role != 'supervisor':
            return HttpResponse("Unauthorized", status=403)

        try:
            student = User.objects.get(id=student_id, role='student')
        except User.DoesNotExist:
            return HttpResponse("Student not found", status=404)

        # Get Date Range from Query Params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # 2. Fetch Logs
        logs = LogEntry.objects.filter(
            student=student,
            date__range=[start_date, end_date]
        ).order_by('date')

        # 3. Create PDF Response
        response = HttpResponse(content_type='application/pdf')
        filename = f"SIWES_Report_{student.username}_{start_date}_to_{end_date}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # 4. Build PDF Content
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        elements.append(Paragraph(f"SIWES Logbook Report", styles['Title']))
        elements.append(Spacer(1, 12))

        # Student Info
        info_text = f"""
        <b>Student Name:</b> {student.first_name} {student.last_name}<br/>
        <b>Matric Number:</b> {student.student_profile.matric_number}<br/>
        <b>Supervisor:</b> {request.user.first_name} {request.user.last_name}<br/>
        <b>Period:</b> {start_date} to {end_date}
        """
        elements.append(Paragraph(info_text, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Table Data
        data = [['Date', 'Time', 'Activity', 'Status']]
        for log in logs:
            # Wrap text to avoid overflow
            activity = Paragraph(log.activities, styles['BodyText'])
            data.append([
                str(log.date),
                f"{log.time_in} - {log.time_out}",
                activity, 
                log.status.title()
            ])

        # Table Style
        table = Table(data, colWidths=[80, 80, 300, 70])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(table)
        
        # 5. Generate
        doc.build(elements)
        return response