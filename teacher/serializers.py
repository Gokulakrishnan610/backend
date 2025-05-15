from rest_framework import serializers
from .models import Teacher, TeacherAvailability
from authentication.serializers import UserSerializer
from department.serializers import DepartmentSerializer

class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for teacher availability slots"""
    day_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TeacherAvailability
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time']
    
    def get_day_name(self, obj):
        return dict(TeacherAvailability.DAYS_OF_WEEK).get(obj.day_of_week)

class TeacherSerializer(serializers.ModelSerializer):
    teacher_id = UserSerializer(read_only=True)
    dept_id = DepartmentSerializer(read_only=True)
    availability_slots = TeacherAvailabilitySerializer(many=True, read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'id', 
            'teacher_id', 
            'dept_id', 
            'staff_code', 
            'teacher_role', 
            'teacher_specialisation', 
            'teacher_working_hours',
            'is_industry_professional',
            'availability_type',
            'availability_slots',
            'resignation_status',
            'resignation_date',
            'is_placeholder',
            'placeholder_description'
        ]
        read_only_fields = ['id', 'is_industry_professional']

class UpdateTeacherSerializer(serializers.ModelSerializer):
    dept_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher._meta.get_field('dept_id').related_model.objects.all(),
        allow_null=True,
        required=False
    )
    
    class Meta:
        model = Teacher
        fields = [
            'dept_id',
            'staff_code',
            'teacher_role',
            'teacher_specialisation',
            'teacher_working_hours',
            'availability_type',
            'resignation_status',
            'resignation_date',
            'is_placeholder',
            'placeholder_description'
        ]
        
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class CreateTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = [
            'teacher_id',
            'dept_id',
            'staff_code',
            'teacher_role',
            'teacher_specialisation',
            'teacher_working_hours',
            'availability_type',
            'resignation_status',
            'resignation_date',
            'is_placeholder',
            'placeholder_description'
        ]
    
    def validate(self, data):
        # Check if teacher role is POP/Industry Professional, set availability type
        if data.get('teacher_role') in ['POP', 'Industry Professional']:
            data['availability_type'] = 'limited'
        return data

# Serializers for TeacherAvailability CRUD operations
class CreateTeacherAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAvailability
        fields = ['teacher', 'day_of_week', 'start_time', 'end_time']
    
    def validate(self, data):
        # Ensure start_time is before end_time
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time")
        
        # Ensure teacher is a POP/industry professional if adding availability
        teacher = data.get('teacher')
        if teacher and not (teacher.is_industry_professional or 
                          teacher.teacher_role in ['POP', 'Industry Professional']):
            if teacher.availability_type == 'limited':
                # Allow limited availability for regular teachers too, but warn
                pass
        return data

class UpdateTeacherAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAvailability
        fields = ['day_of_week', 'start_time', 'end_time']
    
    def validate(self, data):
        # Ensure start_time is before end_time
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time")
        return data