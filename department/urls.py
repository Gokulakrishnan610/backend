from django.urls import path
from .views import DepartmentListCreateView, DepartmentDetailView, DepartmentCoursesView, CurrentDepartmentView

urlpatterns = [
    # Endpoint to list all departments or create a new one
    path('', DepartmentListCreateView.as_view(), name='department-list-create'),
    # Endpoint to retrieve, update or delete a department
    path('<int:pk>/', DepartmentDetailView.as_view(), name='department-detail'),
    # Endpoint to get courses for the current user's department
    path('courses/', DepartmentCoursesView.as_view(), name='department-courses'),
    # Endpoint to get the current user's department
    path('current/', CurrentDepartmentView.as_view(), name='current-department'),
]