from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Room
from unfold.admin import ModelAdmin

class RoomResource(resources.ModelResource):
    class Meta:
        model = Room
        fields = (
            'id',
            'room_number',
            'block',
            'maintained_by_id',
            'is_lab',
            'room_type',
            'room_min_cap',
            'room_max_cap',
            'has_projector',
            'has_ac',
            'tech_level',
            'description',
            'smart_board',
            'green_board',
            'isLcsAvailable',
        )
        export_order = fields

class RoomAdmin(ImportExportModelAdmin, ModelAdmin):
    resource_class = RoomResource
    list_display = ('description','room_number', 'block', 'maintained_by_id', 'is_lab', 'room_type', 'room_min_cap', 'room_max_cap', 'has_projector', 'has_ac','tech_level', 'smart_board', 'green_board', 'isLcsAvailable')
    search_fields = ('room_number', 'block', 'description')
    list_filter = ('block', 'is_lab', 'room_type', 'has_projector', 'has_ac', 'maintained_by_id', 'isLcsAvailable', 'green_board', 'smart_board')
    ordering = ('block', 'room_number')

admin.site.register(Room, RoomAdmin)