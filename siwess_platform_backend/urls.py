from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from logbooks.views import LogBookViewSet, ReportViewSet, GeneratePDFReportView
from accounts.views import DashboardStatsView, AdminStudentViewSet, RegisterView, UserProfileView, SupervisorListView

router = DefaultRouter()
router.register(r'logs', LogBookViewSet, basename='log')
router.register(r'reports', ReportViewSet)
router.register(r'admin/students', AdminStudentViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # Auth Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), # Login
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', RegisterView.as_view(), name='register'),
    
    # Stats
    path('api/dashboard/stats/', DashboardStatsView.as_view()),
    
    path('api/profile/', UserProfileView.as_view()),     
    path('api/supervisors/', SupervisorListView.as_view()), 
    
    path('api/reports/generate/<int:student_id>/', GeneratePDFReportView.as_view(), name='generate-pdf'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)