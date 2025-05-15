# serializers.py
from rest_framework import serializers
from .models import CourseMaster
from department.serializers import DepartmentSerializer

class CourseMasterSerializer(serializers.ModelSerializer):
    course_dept_detail = DepartmentSerializer(source='course_dept_id', read_only=True)
    
    class Meta:
        model = CourseMaster
        fields = [
            'id', 
            'course_id', 
            'course_name', 
            'course_dept_id', 
            'course_dept_detail',
            'is_zero_credit_course',
            'lecture_hours',
            'practical_hours',
            'tutorial_hours',
            'credits',
            'regulation',
            'course_type',
            'degree_type',
        ]