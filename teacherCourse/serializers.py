from rest_framework import serializers
from .models import TeacherCourse
from teacher.serializers import TeacherSerializer
from course.serializers import CourseSerializer

class TeacherCourseSerializer(serializers.ModelSerializer):
    teacher_detail = TeacherSerializer(source='teacher_id', read_only=True)
    course_detail = CourseSerializer(source='course_id', read_only=True)

    class Meta:
        model = TeacherCourse
        fields = [
            'id',
            'teacher_id',
            'teacher_detail',
            'course_id',
            'course_detail',
            'student_count',
            'academic_year',
            'semester',
            'is_assistant',
            'requires_special_scheduling',
            'preferred_availability_slots'
        ]
        extra_kwargs = {
            'teacher_id': {'write_only': True},
            'course_id': {'write_only': True}
        }

    def validate(self, data):
        teacher_id = data.get('teacher_id', self.instance.teacher_id if self.instance else None)
        course_id = data.get('course_id', self.instance.course_id if self.instance else None)
        semester = data.get('semester', self.instance.semester if self.instance else None)

        if not teacher_id or not course_id:
            raise serializers.ValidationError(
                "Both teacher and course are required."
            )

        # Check if teacher has a department assigned
        if not teacher_id.dept_id:
            raise serializers.ValidationError(
                "Teacher must be assigned to a department before being assigned to a course."
            )

        # Check if teacher and course departments match
        if teacher_id.dept_id.id != course_id.teaching_dept_id_id:
            teacher_dept = teacher_id.dept_id.dept_name
            course_dept = course_id.teaching_dept_id.dept_name if course_id.teaching_dept_id else "No Department"
            raise serializers.ValidationError(
                f"Teacher and course must belong to the same department. Teacher's department: {teacher_dept}, Course's teaching department: {course_dept}"
            )

        # Check teacher's working hours
        assigned_courses = TeacherCourse.objects.filter(teacher_id=teacher_id)
        
        # Calculate total hours using the calculate_weekly_hours method
        total_hours_assigned = sum(course.calculate_weekly_hours() for course in assigned_courses)
        
        # Calculate hours for the current course
        current_course_hours = 0
        if course_id and course_id.course_id:
            current_course_hours = course_id.course_id.credits
        
        # Set a flag indicating workload is exceeded, but don't prevent assignment creation
        self._workload_exceeded = (total_hours_assigned + current_course_hours > teacher_id.teacher_working_hours)

        return data