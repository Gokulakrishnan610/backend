from rest_framework import serializers
from .models import Timetable, TimetableChange, TimetableGenerationConfig
from teacher.serializers import TeacherSerializer
from course.serializers import CourseSerializer
from slot.serializers import SlotSerializer
from rooms.serializers import RoomSerializer
from teacherCourse.serializers import TeacherCourseSerializer

class TimetableSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(source='get_teacher', read_only=True)
    course = CourseSerializer(source='get_course', read_only=True)
    slot = SlotSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    day_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Timetable
        fields = '__all__'
        depth = 1


class TimetableWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetable
        fields = '__all__'


class TimetableChangeSerializer(serializers.ModelSerializer):
    original_timetable = TimetableSerializer(read_only=True)
    original_timetable_id = serializers.PrimaryKeyRelatedField(
        queryset=Timetable.objects.all(),
        source='original_timetable',
        write_only=True
    )
    
    class Meta:
        model = TimetableChange
        fields = '__all__'
        extra_kwargs = {
            'created_by': {'required': False}
        }


class TimetableGenerationConfigSerializer(serializers.ModelSerializer):
    """Serializer for timetable generation configurations"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = TimetableGenerationConfig
        fields = [
            'id', 'name', 'created_by', 'created_by_username', 'created_at', 'modified_at',
            'max_teacher_slots_per_day', 'enable_lunch_breaks', 'enable_lab_consecutive',
            'enable_student_conflicts', 'enable_staggered_schedule', 'min_course_instances',
            'division_assignment', 'solver_timeout', 'is_generated', 'generation_started_at',
            'generation_completed_at'
        ]
        read_only_fields = [
            'created_at', 'modified_at', 'is_generated', 'generation_started_at',
            'generation_completed_at', 'generation_log'
        ]
        extra_kwargs = {
            'created_by': {'required': False}
        }
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data) 