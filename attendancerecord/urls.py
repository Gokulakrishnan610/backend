from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, AttendanceSessionViewSet

router = DefaultRouter()
router.register(r'attendance', AttendanceViewSet)
router.register(r'attendance-sessions', AttendanceSessionViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 