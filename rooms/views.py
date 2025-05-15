from rest_framework import generics, status
from rest_framework.response import Response
from .models import Room
from .serializers import RoomSerializer

class RoomListAPIView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def get_queryset(self):
        room_type = self.request.query_params.get('room_type', None)
        if room_type:
            return Room.objects.filter(room_type=room_type)
        return Room.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        room_type = request.query_params.get('room_type', None)
        print("Room type:", room_type)
        if room_type and not queryset.exists():
            return Response(
                {
                    "detail": "No Rooms Found",
                    "code": "no_rooms_found",
                },
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)