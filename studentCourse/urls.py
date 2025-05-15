from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentCourseViewSet, StudentCoursePreferenceViewSet

router = DefaultRouter()
router.register(r'courses', StudentCourseViewSet, basename='student-course')
router.register(r'preferences', StudentCoursePreferenceViewSet, basename='course-preference')

urlpatterns = [
    path('', include(router.urls)),
]