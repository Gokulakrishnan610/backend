from rest_framework import serializers
from .models import Slot, TeacherSlotAssignment

class SlotSerializer(serializers.ModelSerializer):
    slot_type_display = serializers.SerializerMethodField()

    class Meta:
        model = Slot
        fields = ['id', 'slot_name', 'slot_type', 'slot_type_display', 'slot_start_time', 'slot_end_time']
    
    def get_slot_type_display(self, obj):
        return obj.get_slot_type_display()
        
class TeacherSlotAssignmentSerializer(serializers.ModelSerializer):
    slot = SlotSerializer()
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TeacherSlotAssignment
        fields = ['id', 'slot_id', 'day_of_week', 'slot', 'day_name', 'teacher']
        extra_kwargs = {
            'slot_id': {'source': 'slot', 'required': True},
            'day_of_week': {'required': True}
        }

    def get_day_name(self, obj):
        return dict(TeacherSlotAssignment.DAYS_OF_WEEK)[obj.day_of_week]