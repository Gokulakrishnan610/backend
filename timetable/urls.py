from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TimetableViewSet, TimetableChangeViewSet, TimetableGenerationViewSet

router = DefaultRouter()
router.register(r'timetables', TimetableViewSet)
router.register(r'timetable-changes', TimetableChangeViewSet)
router.register(r'timetable-generation', TimetableGenerationViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 