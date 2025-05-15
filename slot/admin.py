from django.contrib import admin
from .models import Slot, TeacherSlotAssignment
from django.db.models import Count, Q
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .resources import TeacherSlotResource
from import_export.admin import ImportExportModelAdmin

@admin.register(Slot)
class SlotAdmin(ModelAdmin):
    list_display = ('id','slot_name', 'slot_type', 'slot_time_range', 'total_assignments')
    list_filter = ('slot_type',)
    search_fields = ('slot_name',)
    
    def slot_time_range(self, obj):
        return f"{obj.slot_start_time.strftime('%H:%M')} - {obj.slot_end_time.strftime('%H:%M')}"
    slot_time_range.short_description = "Time Range"
    
    def total_assignments(self, obj):
        return obj.teacher_assignments.count()
    total_assignments.short_description = "Total Assignments"

class DayOfWeekFilter(admin.SimpleListFilter):
    title = 'Day of Week'
    parameter_name = 'day_of_week'
    
    def lookups(self, request, model_admin):
        return TeacherSlotAssignment.DAYS_OF_WEEK
    
    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(day_of_week=self.value())
        return queryset

class SlotTypeFilter(admin.SimpleListFilter):
    title = 'Slot Type'
    parameter_name = 'slot_type'
    
    def lookups(self, request, model_admin):
        return Slot.SLOT_TYPES
    
    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(slot__slot_type=self.value())
        return queryset

@admin.register(TeacherSlotAssignment)
class TeacherSlotAssignmentAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ('teacher', 'department', 'day_name', 'slot_info', 'assignment_status')
    list_filter = (DayOfWeekFilter, SlotTypeFilter, 'teacher__dept_id')
    search_fields = ('teacher__teacher_id__first_name', 'teacher__teacher_id__last_name', 'teacher__staff_code')
    autocomplete_fields = ('teacher', 'slot')
    resource_classes = [TeacherSlotResource]

    def department(self, obj):
        if obj.teacher.dept_id:
            return obj.teacher.dept_id.dept_name
        return "-"
    department.short_description = "Department"
    
    def day_name(self, obj):
        return dict(TeacherSlotAssignment.DAYS_OF_WEEK)[obj.day_of_week]
    day_name.short_description = "Day"  
    
    def slot_info(self, obj):
        return f"{obj.slot.slot_name} ({obj.slot.get_slot_type_display()}: {obj.slot.slot_start_time.strftime('%H:%M')} - {obj.slot.slot_end_time.strftime('%H:%M')})"
    slot_info.short_description = "Slot"
    
    def assignment_status(self, obj):
        # Check for issues
        teacher = obj.teacher
        dept_id = teacher.dept_id.id if teacher.dept_id else None
        
        if dept_id:
            # Calculate department distribution
            total_dept_teachers = teacher.dept_id.department_teachers.count()
            day_assignments = TeacherSlotAssignment.objects.filter(
                teacher__dept_id=dept_id,
                day_of_week=obj.day_of_week,
                slot__slot_type=obj.slot.slot_type
            ).count()
            
            if day_assignments > int(total_dept_teachers * 0.33 + 0.5) and total_dept_teachers > 0:
                return format_html('<span style="color: red; font-weight: bold">⚠️ Exceeds 33% Dept. Allocation</span>')
        
        # Check if teacher exceeds 5 days
        days_assigned = TeacherSlotAssignment.objects.filter(
            teacher=teacher
        ).values('day_of_week').distinct().count()
        
        if days_assigned > 5:
            return format_html('<span style="color: red; font-weight: bold">⚠️ Exceeds 5 days limit</span>')
            
        return format_html('<span style="color: green">✓ Valid</span>')
    assignment_status.short_description = "Status"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher', 'teacher__dept_id', 'slot')