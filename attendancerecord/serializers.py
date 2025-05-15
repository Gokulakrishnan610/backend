from rest_framework import serializers
from .models import Attendance, AttendanceSession
from student.serializers import StudentSerializer
from teacher.serializers import TeacherSerializer
from timetable.serializers import TimetableSerializer

class AttendanceSessionSerializer(serializers.ModelSerializer):
    timetable_slot = TimetableSerializer(read_only=True)
    conducted_by = TeacherSerializer(read_only=True)
    substitute_teacher = TeacherSerializer(read_only=True)
    
    class Meta:
        model = AttendanceSession
        fields = '__all__'


class AttendanceSessionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSession
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    timetable_slot = TimetableSerializer(read_only=True)
    marked_by = TeacherSerializer(read_only=True)
    
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class BulkAttendanceSerializer(serializers.Serializer):
    timetable_slot_id = serializers.IntegerField()
    date = serializers.DateField()
    marked_by_id = serializers.IntegerField()
    attendance_data = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
        )
    ) 