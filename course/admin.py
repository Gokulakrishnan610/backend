from django.contrib import admin
from .models import Course, CourseResourceAllocation, CourseSlotPreference, CourseRoomPreference
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from .resources import CourseResource

class CourseAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = (
        'get_course_id', 
        'get_course_name',
        'course_year', 
        'course_semester', 
        'get_regulation', 
        'get_course_type', 
        'get_credits',
        'teaching_dept_id'
    )
    resource_classes = [CourseResource]
    search_fields = ('course_id__course_id', 'course_id__course_name')
    list_filter = (
        'course_id__course_dept_id', 
        'course_year', 
        'course_semester', 
        'course_id__regulation', 
        'course_id__course_type',
        'elective_type',
        'teaching_dept_id'
    )
    ordering = ('course_id__course_id',)
    
    def get_course_id(self, obj):
        return obj.course_id.course_id
    get_course_id.short_description = 'Course ID'
    get_course_id.admin_order_field = 'course_id__course_id'
    
    def get_course_name(self, obj):
        return obj.course_id.course_name
    get_course_name.short_description = 'Course Name'
    get_course_name.admin_order_field = 'course_id__course_name'
    
    def get_regulation(self, obj):
        return obj.course_id.regulation
    get_regulation.short_description = 'Regulation'
    get_regulation.admin_order_field = 'course_id__regulation'
    
    def get_course_type(self, obj):
        return obj.course_id.course_type
    get_course_type.short_description = 'Course Type'
    get_course_type.admin_order_field = 'course_id__course_type'
    
    def get_credits(self, obj):
        return obj.course_id.credits
    get_credits.short_description = 'Credits'
    get_credits.admin_order_field = 'course_id__credits'

class CourseResourceAllocationAdmin(ModelAdmin):
    list_display = ('course_id', 'original_dept_id', 'teaching_dept_id', 'allocation_date', 'status')
    list_filter = ('status', 'allocation_date', 'original_dept_id', 'teaching_dept_id')
    search_fields = ('course_id__course_id__course_id', 'course_id__course_id__course_name')
    date_hierarchy = 'allocation_date'

class CourseSlotPreferenceAdmin(ModelAdmin):
    list_display = ('course_id', 'slot_id', 'preference_level')
    list_filter = ('slot_id', 'preference_level')
    search_fields = ('course_id__course_id__course_id', 'course_id__course_id__course_name')

class CourseRoomPreferenceAdmin(ModelAdmin):
    list_display = ('course_id', 'room_id', 'preference_level', 'preferred_for', 'tech_level_preference')
    list_filter = ('room_id', 'preference_level', 'preferred_for', 'tech_level_preference')
    search_fields = ('course_id__course_id__course_id', 'course_id__course_id__course_name', 'room_id__room_number')

admin.site.register(Course, CourseAdmin)
admin.site.register(CourseResourceAllocation, CourseResourceAllocationAdmin)
admin.site.register(CourseSlotPreference, CourseSlotPreferenceAdmin)
admin.site.register(CourseRoomPreference, CourseRoomPreferenceAdmin)