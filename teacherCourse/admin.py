from django.contrib import admin
from django import forms
from django.db.models import Q
from .models import TeacherCourse
from unfold.admin import ModelAdmin

class TeacherCourseForm(forms.ModelForm):
    """Custom form to handle POP/industry professional scheduling"""
    class Meta:
        model = TeacherCourse
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we have an instance (editing existing)
        if self.instance and self.instance.pk:
            # If the teacher is an industry professional, only show their availability slots
            if hasattr(self.instance, 'teacher_id') and self.instance.teacher_id:
                teacher = self.instance.teacher_id
                if teacher.is_industry_professional or teacher.teacher_role == 'POP':
                    self.fields['preferred_availability_slots'].queryset = teacher.availability_slots.all()
                    self.fields['preferred_availability_slots'].required = True
        
        # The availability slots field should only be visible for industry professionals
        if 'teacher_id' in self.data:
            try:
                teacher_id = int(self.data.get('teacher_id'))
                from teacher.models import Teacher
                teacher = Teacher.objects.get(pk=teacher_id)
                if teacher.is_industry_professional or teacher.teacher_role == 'POP':
                    self.fields['preferred_availability_slots'].queryset = teacher.availability_slots.all()
                    self.fields['preferred_availability_slots'].required = True
            except (ValueError, TypeError, Teacher.DoesNotExist):
                pass

class TeacherCourseAdmin(ModelAdmin):
    form = TeacherCourseForm
    list_display = ('teacher_id', 'course_id', 'academic_year', 'semester', 'student_count', 'requires_special_scheduling')
    list_filter = ('academic_year', 'semester', 'teacher_id__dept_id', 'course_id__course_id', 'requires_special_scheduling', 'teacher_id__is_industry_professional')
    search_fields = ('teacher_id__teacher_id__email', 'course_id__course_id__course_id', 'course_id__course_id__course_name')
    filter_horizontal = ('preferred_availability_slots',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('teacher_id', 'course_id', 'academic_year', 'semester', 'student_count')
        }),
        ('Special Scheduling', {
            'fields': ('requires_special_scheduling', 'preferred_availability_slots'),
            'classes': ('collapse',),
            'description': 'Use this section when scheduling industry professionals or POPs'
        }),
    )
    
    def get_queryset(self, request):
        """Custom queryset to add annotation for identifying industry professional courses"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('teacher_id', 'course_id')
        return queryset
    
    def get_readonly_fields(self, request, obj=None):
        """Make requires_special_scheduling readonly as it's set automatically"""
        readonly = ['requires_special_scheduling']
        return readonly
    
    def save_model(self, request, obj, form, change):
        """Additional validation before saving"""
        # Make sure special scheduling is set for industry professionals
        if obj.teacher_id and (obj.teacher_id.is_industry_professional or obj.teacher_id.teacher_role == 'POP'):
            obj.requires_special_scheduling = True
        super().save_model(request, obj, form, change)

admin.site.register(TeacherCourse, TeacherCourseAdmin)
