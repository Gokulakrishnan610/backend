from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import StudentCourse

class StudentCourseAdmin(ModelAdmin):
    list_display = ('student_id', 'course_id')
    list_filter = ('course_id__course_id', 'student_id__dept_id')
    search_fields = ('student_id__student_id__email', 'course_id__course_id__course_id', 'course_id__course_id__course_name')

admin.site.register(StudentCourse, StudentCourseAdmin)
