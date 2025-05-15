from rest_framework import serializers
from .models import StudentCourse, StudentCoursePreference
from teacher.serializers import TeacherSerializer
from course.serializers import CourseSerializer
from student.serializers import StudentSerializer
from slot.serializers import SlotSerializer

class StudentCoursePreferenceSerializer(serializers.ModelSerializer):
    teacher_details = TeacherSerializer(source='teacher_id', read_only=True)
    
    class Meta:
        model = StudentCoursePreference
        fields = ['id', 'teacher_id', 'teacher_details', 'preference_order', 'created_at']
        read_only_fields = ['created_at']

class StudentCourseSerializer(serializers.ModelSerializer):
    student_details = StudentSerializer(source='student_id', read_only=True)
    course_details = CourseSerializer(source='course_id', read_only=True)
    teacher_details = TeacherSerializer(source='teacher_id', read_only=True)
    slot_details = SlotSerializer(source='slot_id', read_only=True)
    preferences = StudentCoursePreferenceSerializer(many=True, read_only=True)

    class Meta:
        model = StudentCourse
        fields = [
            'id', 'student_id', 'student_details',
            'course_id', 'course_details',
            'teacher_id', 'teacher_details',
            'slot_id', 'slot_details',
            'status', 'created_at', 'updated_at',
            'preferences'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        # Check for time slot conflicts
        student = data.get('student_id')
        slot = data.get('slot_id')
        if student and slot:
            conflicts = StudentCourse.objects.filter(
                student_id=student,
                slot_id=slot,
                status='approved'
            )
            if self.instance:
                conflicts = conflicts.exclude(id=self.instance.id)
            if conflicts.exists():
                raise serializers.ValidationError("This time slot conflicts with another course")
        
        # Check if teacher teaches this course
        teacher = data.get('teacher_id')
        course = data.get('course_id')
        if teacher and course:
            if not teacher.teachercourse_set.filter(course_id=course).exists():
                raise serializers.ValidationError("Selected teacher does not teach this course")
        
        return data