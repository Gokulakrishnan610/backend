from django.urls import path
from .views import RoomListAPIView

urlpatterns = [
    path('', RoomListAPIView.as_view(), name='room-list'),
] 