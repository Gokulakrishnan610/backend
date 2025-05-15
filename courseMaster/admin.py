# from django.contrib import admin
# from .models import CourseMaster
# from unfold.admin import ModelAdmin



# @admin.register(CourseMaster)
# class CourseMasterAdmin(ModelAdmin):
#     list_display = ('course_id', 'course_name', 'course_dept_id')
#     search_fields = ('course_id', 'course_name')
#     list_filter = ('course_dept_id',)




from django.contrib import admin
from .models import CourseMaster
from department.models import Department
from unfold.admin import ModelAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .resources import CourseMasterResource


@admin.register(CourseMaster)
class CourseMasterAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = CourseMasterResource

    list_display = (
        'course_id',
        'course_name',
        'course_dept_id',
        'credits',       # Corrected from course_credits
        'course_type',
        'degree_type'
    )

    search_fields = (
        'course_id',
        'course_name',
    )

    list_filter = (
        'course_dept_id',
        'course_type',
        'degree_type'
    )

    ordering = ('course_id',)
