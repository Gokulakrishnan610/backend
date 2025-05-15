from rest_framework import serializers
from .models import Room
from department.serializers import DepartmentSerializer

class RoomSerializer(serializers.ModelSerializer):
    maintained_by_detail = DepartmentSerializer(source='maintained_by_id', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id',
            'room_number',
            'block',
            'description',
            'maintained_by_id',
            'maintained_by_detail',
            'is_lab',
            'room_type',
            'room_min_cap',
            'room_max_cap',
            'has_projector',
            'has_ac',
            'tech_level'
        ] 