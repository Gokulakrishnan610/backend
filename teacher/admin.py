from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Teacher, TeacherAvailability
from unfold.admin import StackedInline
from django.db.models import Q
from django.contrib import messages
from import_export import fields

class TeacherResource(resources.ModelResource):
    # email = fields.Field(attribute='teacher_id__email', column_name='Email')
    # first_name = fields.Field(attribute='teacher_id__first_name', column_name='First Name')
    # last_name = fields.Field(attribute='teacher_id__last_name', column_name='Last Name')
    # department = fields.Field(attribute='dept_id__dept_name', column_name='Department')
    # working_hours = fields.Field(attribute='teacher_working_hours', column_name='Working Hours')

    class Meta:
        model = Teacher
        fields = (
            'id',
            'email',
            'teacher_id__first_name',
            'teacher_id__last_name',
            'dept_id',
            'staff_code',
            'teacher_role',
            # 'working_hours',  # Use the renamed field
            # 'availability_type',
            'is_industry_professional',
            'resignation_status',
        )
        export_order = fields

    # def dehydrate_working_hours(self, teacher):
    #     # Ensure the value is exported as string to avoid decimal conversion
    #     return str(teacher.teacher_working_hours)
        
class TeacherAvailabilityInline(admin.TabularInline):
    model = TeacherAvailability
    extra = 0
    fields = ('day_of_week', 'start_time', 'end_time')

class TeacherAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = TeacherResource
    inlines = [TeacherAvailabilityInline]

    list_display = ( 'teacher_name', 'dept_id', 'staff_code', 'teacher_role', 'teacher_specialisation', 
                    'teacher_working_hours', 'is_industry_professional', 'availability_type', 'is_placeholder', 'resignation_status')
    search_fields = ('teacher_id__email', 'teacher_id__first_name', 'teacher_id__last_name', 'staff_code', 'teacher_specialisation')
    list_filter = ('dept_id', 'teacher_working_hours', 'teacher_role', 'is_industry_professional', 'availability_type', 'is_placeholder', 'resignation_status')
    ordering = ('staff_code',)
    
    # Group fields in fieldsets
    fieldsets = (
        ('Basic Information', {
            'fields': ('teacher_id', 'dept_id', 'staff_code', 'teacher_role')
        }),
        ('Teaching Details', {
            'fields': ('teacher_specialisation', 'teacher_working_hours')
        }),
        ('Availability', {
            'fields': ('availability_type', 'is_industry_professional'),
            'classes': ('collapse',),
            'description': 'Industry professionals/POPs need specific availability slots defined'
        }),
        ('Status', {
            'fields': ('resignation_status', 'resignation_date', 'is_placeholder', 'placeholder_description'),
            'description': 'Manage teacher status including placeholders for future positions'
        }),
    )
    
    def teacher_name(self, obj):
        """Display teacher's full name"""
        return f"{obj}"
    teacher_name.short_description = 'Teacher Name'

    def get_readonly_fields(self, request, obj=None):
        """Make is_industry_professional readonly as it's set automatically based on role"""
        return ('is_industry_professional',)

    def save_model(self, request, obj, form, change):
        """Additional validation before saving"""
        # Make sure industry professionals have limited availability
        if obj.is_industry_professional or obj.teacher_role in ['POP', 'Industry Professional']:
            obj.availability_type = 'limited'
            obj.is_industry_professional = True
            
        # Check for unique roles
        unique_roles = ['Dean', 'Principal', 'Vice Principal', 'Physical Director']
        if obj.teacher_role in unique_roles:
            existing = Teacher.objects.filter(teacher_role=obj.teacher_role).exclude(pk=obj.pk if obj.pk else None)
            if existing.exists():
                role_display = dict(Teacher.TEACHER_ROLES).get(obj.teacher_role, obj.teacher_role)
                self.message_user(
                    request,
                    f"Warning: There is already a {role_display} in the institution.",
                    level=messages.WARNING
                )
        
        super().save_model(request, obj, form, change)


class TeacherResigingProxy(Teacher):
    class Meta:
        proxy = True
        verbose_name = "Resigning Teacher"

@admin.register(TeacherResigingProxy)
class ResigingTeachers(ModelAdmin):
    list_display = ('teacher_id', 'dept_id', 'staff_code', 'teacher_role', 'teacher_specialisation', 
                    'teacher_working_hours', 'is_industry_professional', 'availability_type', 'is_placeholder', 'resignation_status')
    
    def get_queryset(self, request):
        queryset = Teacher.objects.filter(resignation_status__in=['resigning', 'resigned'])
        return queryset
    
class PlaceholderProxy(Teacher):
    class Meta:
        proxy = True
        verbose_name = "Placeholders"

@admin.register(PlaceholderProxy)
class PlaceholderAdmin(ModelAdmin):
    list_display = ('teacher_id', 'dept_id', 'staff_code', 'teacher_role', 'teacher_specialisation', 
                    'teacher_working_hours', 'is_industry_professional', 'availability_type', 'is_placeholder', 'resignation_status')
    
    def get_queryset(self, request):
        queryset = Teacher.objects.filter(is_placeholder=True)
        return queryset

class TeacherInline(StackedInline):
    model = Teacher
    extra = 1
    max_num = 1
    can_delete = False
    verbose_name_plural = 'Teacher Details'
    fieldsets = (
        ('Basic Information', {
            'fields': ('dept_id', 'staff_code', 'teacher_role')
        }),
        ('Teaching Details', {
            'fields': ('teacher_specialisation', 'teacher_working_hours')
        }),
        ('Status', {
            'fields': ('resignation_status', 'is_placeholder')
        }),
    )

admin.site.register(Teacher, TeacherAdmin)
admin.site.register(TeacherAvailability)