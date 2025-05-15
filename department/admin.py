from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Department
from unfold.admin import ModelAdmin

class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        fields = (
            'id',
            'dept_name',
            'date_established',
            'contact_info',
        )
        export_order = fields

class DepartmentAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = DepartmentResource

    list_display = ('id','dept_name', 'date_established', 'contact_info')
    search_fields = ('dept_name', 'contact_info')
    list_filter = ('date_established',)
    ordering = ('dept_name',)

admin.site.register(Department, DepartmentAdmin)