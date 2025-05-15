from django.contrib import admin
from .models import Timetable, TimetableChange
from unfold.admin import ModelAdmin
from django import forms

class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You could add custom field behavior here if needed

class TimetableAdmin(ModelAdmin):
    form = TimetableForm
    list_display = ('day_name', 'session_type', 'get_course_name', 'get_teacher_name', 'slot', 'room', 'is_recurring')
    list_filter = ('day_of_week', 'session_type', 'is_recurring', 'start_date', 'course_assignment__course_id__course_semester')
    search_fields = (
        'course_assignment__course_id__course_id__course_name', 
        'course_assignment__teacher_id__teacher_id__first_name',
        'course_assignment__teacher_id__teacher_id__last_name',
        'room__room_number'
    )
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('day_of_week', 'slot', 'room', 'session_type'),
            'description': 'Define when and where the class will take place'
        }),
        ('Course Assignment', {
            'fields': ('course_assignment',),
            'description': 'Select the teacher-course assignment'
        }),
        ('Schedule Duration', {
            'fields': ('is_recurring', 'start_date', 'end_date'),
            'description': 'Define if this is a recurring class and specify the date range'
        }),
    )
    
    def get_course_name(self, obj):
        return obj.course_assignment.course_id.course_id.course_name
    get_course_name.short_description = 'Course'
    get_course_name.admin_order_field = 'course_assignment__course_id__course_id__course_name'
    
    def get_teacher_name(self, obj):
        teacher = obj.course_assignment.teacher_id
        if teacher.teacher_id:
            return f"{teacher.teacher_id.first_name} {teacher.teacher_id.last_name}"
        return "N/A"
    get_teacher_name.short_description = 'Teacher'
    get_teacher_name.admin_order_field = 'course_assignment__teacher_id__teacher_id__first_name'


class TimetableChangeAdmin(ModelAdmin):
    list_display = ('original_timetable', 'effective_from', 'effective_to', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'effective_from', 'created_at')
    search_fields = ('reason', 'created_by__email', 'original_timetable__course_assignment__course_id__course_id__course_name')
    date_hierarchy = 'effective_from'
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Original Timetable', {
            'fields': ('original_timetable',),
            'description': 'Select the timetable entry to be changed'
        }),
        ('Requested Changes', {
            'fields': ('new_day_of_week', 'new_slot', 'new_room'),
            'description': 'Specify the changes to be made'
        }),
        ('Change Details', {
            'fields': ('reason', 'effective_from', 'effective_to', 'created_by', 'status'),
            'description': 'Specify the reason and validity period of the change'
        }),
    )

admin.site.register(Timetable, TimetableAdmin)
admin.site.register(TimetableChange, TimetableChangeAdmin)
