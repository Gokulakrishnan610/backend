from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Student
from unfold.admin import ModelAdmin, StackedInline

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        fields = (
            'id',
            'student_id__email',
            'student_id__first_name',
            'student_id__last_name',
            'batch',
            'current_semester',
        )
        export_order = fields  

class StudentAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = StudentResource 

    list_display = ('id', 'student_id', 'batch', 'current_semester', 'year', 'dept_id', 'roll_no', 'student_type', 'degree_type')
    search_fields = ('student_id__email', 'student_id__first_name', 'student_id__last_name', 'roll_no')
    list_filter = ('batch', 'current_semester', 'year', 'dept_id', 'student_type', 'degree_type')
    ordering = ('batch', 'student_id__first_name')

class StudentAdminInline(StackedInline):
    model = Student
    extra = 1
    max_num = 1
    can_delete = False
    verbose_name_plural = 'Student Details'
    fieldsets = (
        (None, {
            'fields': ('batch', 'current_semester', 'year', 'dept_id', 'roll_no', 'student_type', 'degree_type')
        }),
    )
admin.site.register(Student, StudentAdmin)