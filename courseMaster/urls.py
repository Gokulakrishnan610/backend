from django.urls import path
from .views import CourseMasterListAPIView, CourseMasterDetailAPIView, CourseMasterStatsAPIView

urlpatterns = [
    path('', CourseMasterListAPIView.as_view(), name='course-master'),
    path('<int:pk>/', CourseMasterDetailAPIView.as_view()),
    path('stats/', CourseMasterStatsAPIView.as_view(), name='course-master-stats'),
]