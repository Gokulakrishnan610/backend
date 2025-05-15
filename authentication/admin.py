from django.contrib import admin
from unfold.admin import ModelAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import User, ForgetPassword, BlockedStudents
from student.admin import StudentAdminInline
from teacher.admin import TeacherInline

# User Resource
class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'is_staff',
            'is_superuser',
            'user_type',
            'gender',
            'phone_number',
            'last_login',
            'date_joined',
        )
        export_order = fields

# User Admin
@admin.register(User)
class CustomUserAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = UserResource
    inlines = []

    list_display = ('email', 'name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'user_type', 'gender')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password', 'user_type')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'gender')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )


    def name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    name.short_description = 'Name'

    def get_inline_instances(self, request, obj = ...):
        if not obj:
            return []
        
        self.inlines = []

        if obj.user_type == 'student':
            self.inlines = [StudentAdminInline]
        elif obj.user_type == 'teacher':
            self.inlines = [TeacherInline]

        return super().get_inline_instances(request, obj)

    def save_model(self, request, obj, form, change):
        if not change and 'password' in form.cleaned_data:
            obj.set_password(form.cleaned_data['password'])
        obj.save()

# ForgetPassword Admin
@admin.register(ForgetPassword)
class ForgetPasswordAdmin(ImportExportModelAdmin, ModelAdmin):
    list_display = ('user_id', 'code')
    search_fields = ('user_id__email', 'code')

# BlockedStudents Resource
class BlockedStudentsResource(resources.ModelResource):
    class Meta:
        model = BlockedStudents
        fields = ('id', 'email', 'name', 'dept', 'year')
        export_order = fields

# BlockedStudents Admin
@admin.register(BlockedStudents)
class BlockedStudentsAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = BlockedStudentsResource

    list_display = ('email', 'name', 'dept', 'year')
    search_fields = ('email', 'name', 'dept')
    list_filter = ('dept', 'year')