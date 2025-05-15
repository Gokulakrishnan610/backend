from import_export import resources
from .models import TeacherSlotAssignment

class TeacherSlotResource(resources.ModelResource):
    class Meta:
        model = TeacherSlotAssignment
        skip_unchanged = True
        report_skipped = True
        fields = (
            'teacher__teacher_id',
            'slot__slot_name',
            'day_of_week',
    )