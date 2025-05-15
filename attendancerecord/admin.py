from django.contrib import admin
from .models import Attendance, AttendanceSession
from unfold.admin import ModelAdmin
from django import forms
from django.urls import reverse
from django.utils.html import format_html

class AttendanceSessionForm(forms.ModelForm):
    class Meta:
        model = AttendanceSession
        fields = '__all__'

class AttendanceSessionAdmin(ModelAdmin):
    form = AttendanceSessionForm
    list_display = ('get_course_name', 'get_teacher_name', 'date', 'status', 'get_substitute_teacher')
    list_filter = ('status', 'date', 'conducted_by', 'timetable_slot__course_assignment__course_id__course_semester')
    search_fields = (
        'timetable_slot__course_assignment__course_id__course_id__course_name', 
        'conducted_by__teacher_id__first_name',
        'conducted_by__teacher_id__last_name',
        'substitute_teacher__teacher_id__first_name',
        'substitute_teacher__teacher_id__last_name'
    )
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('timetable_slot', 'date', 'status'),
            'description': 'Basic information about the class session'
        }),
        ('Teachers', {
            'fields': ('conducted_by', 'substitute_teacher'),
            'description': 'Specify who conducted the class'
        }),
        ('Cancellation Details', {
            'fields': ('cancel_reason',),
            'description': 'Provide a reason if the class was cancelled',
            'classes': ('collapse',),
        }),
    )
    
    def get_course_name(self, obj):
        return obj.timetable_slot.course_assignment.course_id.course_id.course_name
    get_course_name.short_description = 'Course'
    get_course_name.admin_order_field = 'timetable_slot__course_assignment__course_id__course_id__course_name'
    
    def get_teacher_name(self, obj):
        teacher = obj.conducted_by
        if teacher.teacher_id:
            return f"{teacher.teacher_id.first_name} {teacher.teacher_id.last_name}"
        return "N/A"
    get_teacher_name.short_description = 'Teacher'
    get_teacher_name.admin_order_field = 'conducted_by__teacher_id__first_name'
    
    def get_substitute_teacher(self, obj):
        if not obj.substitute_teacher:
            return "-"
        teacher = obj.substitute_teacher
        if teacher.teacher_id:
            return f"{teacher.teacher_id.first_name} {teacher.teacher_id.last_name}"
        return "N/A"
    get_substitute_teacher.short_description = 'Substitute'
    
    def get_inline_instances(self, request, obj=None):
        if obj:
            # Only show inline if session already exists
            self.inlines = [AttendanceInline]
        else:
            self.inlines = []
        return super().get_inline_instances(request, obj)


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    fields = ('student', 'status', 'remarks')
    readonly_fields = ('time_marked',)
    can_delete = True
    show_change_link = True


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceAdmin(ModelAdmin):
    form = AttendanceForm
    list_display = ('student', 'get_course_name', 'date', 'status', 'marked_by', 'time_marked')
    list_filter = ('status', 'date', 'marked_by', 'timetable_slot__course_assignment__course_id__course_semester')
    search_fields = (
        'student__student_id__first_name',
        'student__student_id__last_name',
        'timetable_slot__course_assignment__course_id__course_id__course_name',
        'remarks'
    )
    date_hierarchy = 'date'
    readonly_fields = ('time_marked', 'get_session_link')
    
    fieldsets = (
        ('Attendance Information', {
            'fields': ('student', 'timetable_slot', 'date', 'status'),
            'description': 'Basic attendance information'
        }),
        ('Additional Details', {
            'fields': ('marked_by', 'time_marked', 'remarks', 'get_session_link'),
            'description': 'Information about who marked the attendance and when'
        }),
    )
    
    def get_course_name(self, obj):
        return obj.timetable_slot.course_assignment.course_id.course_id.course_name
    get_course_name.short_description = 'Course'
    get_course_name.admin_order_field = 'timetable_slot__course_assignment__course_id__course_id__course_name'
    
    def get_session_link(self, obj):
        """Provide a link to the related attendance session"""
        session = obj.session
        if not session:
            return "No session found"
        
        url = reverse('admin:attendancerecord_attendancesession_change', args=[session.id])
        return format_html('<a href="{}">View Session</a>', url)
    get_session_link.short_description = 'Related Session'


admin.site.register(AttendanceSession, AttendanceSessionAdmin)
admin.site.register(Attendance, AttendanceAdmin)
