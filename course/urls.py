from django.urls import path
from .views import (
    CourseListView, 
    CourseDetailView, 
    CourseResourceAllocationListCreateView, 
    CourseResourceAllocationDetailView,
    CourseRoomPreferenceListCreateView,
    CourseRoomPreferenceDetailView,
    CourseAssignmentStatsView,
    CourseNotification,
)

urlpatterns = [
    path('', CourseListView.as_view(), name='course-list'),
    path('<int:id>/', CourseDetailView.as_view(), name='course-detail'),
    path('resource-allocation/', CourseResourceAllocationListCreateView.as_view(), name='resource-allocation-list'),
    path('resource-allocation/<int:id>/', CourseResourceAllocationDetailView.as_view(), name='resource-allocation-detail'),
    path('<int:course_id>/room-preferences/', CourseRoomPreferenceListCreateView.as_view(), name='course-room-preference-list'),
    path('<int:course_id>/room-preferences/<int:id>/', CourseRoomPreferenceDetailView.as_view(), name='course-room-preference-detail'),
    path('stats/', CourseAssignmentStatsView.as_view(), name='course-assignment-stats'),
    path('stats/<int:course_id>/', CourseAssignmentStatsView.as_view(), name='course-assignment-stats-detail'),
    path('course-notification/', CourseNotification.as_view(), name='course-notification'),
]