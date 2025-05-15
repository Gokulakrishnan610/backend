from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for viewsets
router = DefaultRouter()
router.register(r'availability', views.TeacherAvailabilityViewSet, basename='teacher-availability')

urlpatterns = [
    path('', views.TeacherListView.as_view(), name='teacher-list'),
    path('add/', views.AddNewTeacher.as_view(), name='add-teacher'),
    path('<int:id>/', views.TeacherDetailView.as_view(), name='teacher-detail'),
    
    path('pop/', views.TeacherListView.as_view(queryset=views.Teacher.objects.filter(teacher_role='POP')), name='pop-teacher-list'),
    path('industry-professionals/', views.TeacherListView.as_view(queryset=views.Teacher.objects.filter(is_industry_professional=True)), name='industry-professional-list'),
    
    # New endpoints for resignation management and placeholder teachers
    path('placeholder/create/', views.CreatePlaceholderTeacher.as_view(), name='create-placeholder-teacher'),
    path('resigning/', views.TeacherListView.as_view(queryset=views.Teacher.objects.filter(resignation_status='resigning')), name='resigning-teachers'),
    path('resigned/', views.TeacherListView.as_view(queryset=views.Teacher.objects.filter(resignation_status='resigned')), name='resigned-teachers'),
    path('placeholders/', views.TeacherListView.as_view(queryset=views.Teacher.objects.filter(is_placeholder=True)), name='placeholder-teachers'),
    
    path('', include(router.urls)),
]