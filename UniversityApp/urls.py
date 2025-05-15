"""
URL configuration for UniversityApp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from utlis.views import ImportDataView
from django.conf import settings

# Simple health check view
def health_check(request):
    return JsonResponse({"status": "ok", "message": "API is running"})

# Test authentication and permissions
def auth_debug(request):
    """Debug endpoint to check authentication without requiring auth"""
    user_info = {
        'is_authenticated': request.user.is_authenticated,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'username': request.user.username if request.user.is_authenticated else None,
    }
    
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    return JsonResponse({
        "status": "ok", 
        "message": "API debug info", 
        "user": user_info,
        "auth_header": auth_header,
        "method": request.method,
        "path": request.path,
    })

# API URL patterns with a prefix
api_urlpatterns = [
    path('auth/', include('authentication.urls')),
    path('teachers/', include('teacher.urls')),
    path('course/', include('course.urls')),
    path('teacher-courses/', include('teacherCourse.urls')),
    path('student-courses/', include('studentCourse.urls')),
    path('students/', include('student.urls')),
    path("department/", include('department.urls')),
    path("course-master/", include("courseMaster.urls")),
    path("slots/", include('slot.urls')),
    path('rooms/', include('rooms.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('timetable/', include('timetable.urls')),
    path('attendance/', include('attendancerecord.urls')),
    path('import/<str:resource_name>/', ImportDataView.as_view(), name="import-resource"),
    # Health check endpoint
    path('health/', health_check, name='health_check'),
    # Debug endpoint
    path('debug/', auth_debug, name='auth_debug'),
]

# API_PATH = '/' if settings.ENVIRONMENT == 'production' else 'api/'

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include all API endpoints under 'api/' prefix
    path('api/', include(api_urlpatterns)),
]