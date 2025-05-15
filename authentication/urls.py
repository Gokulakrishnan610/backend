from django.urls import path
from .views import *

urlpatterns = [
    path("new/", CreateNewUserAPIView.as_view(), name="new-user"),
    path('login/', LoginAPIView.as_view(), name='login'),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path('forgot_password/', ForgotPasswordAPI.as_view(), name='forget-password'),
    path('logout/', LogoutAPIView.as_view(), name="logout"),
    path('csrf_token/', CsrfTokenAPIView.as_view(), name="csrf-token"),
    path('status/', AuthStatusAPIView.as_view(), name="auth-status"),
]