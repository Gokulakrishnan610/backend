from django.urls import path
from .views import TeacherCourseListView, TeacherCourseDetailView, TeacherAssignmentsByTeacherView

urlpatterns = [
    path('', TeacherCourseListView.as_view(), name='teacher-course-list'),
    path('<int:pk>/', TeacherCourseDetailView.as_view(), name='teacher-course-detail'),
    path('teacher/<int:teacher_id>/', TeacherAssignmentsByTeacherView.as_view(), name='teacher-assignments'),
]