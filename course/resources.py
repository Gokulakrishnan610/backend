# resources.py
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, BooleanWidget
from .models import Course
from courseMaster.models import CourseMaster
from department.models import Department

class CourseResource(resources.ModelResource):
    course_id = fields.Field(
        column_name='course_id',
        attribute='course_id',
        widget=ForeignKeyWidget(CourseMaster, 'course_id')
    )
    
    for_dept_id = fields.Field(
        column_name='for_dept_id',
        attribute='for_dept_id',
        widget=ForeignKeyWidget(Department, 'dept_name'),
        default=None
    )
    
    teaching_dept_id = fields.Field(
        column_name='teaching_dept_id',
        attribute='teaching_dept_id',
        widget=ForeignKeyWidget(Department, 'dept_name'),
        default=None
    )
    
    # Boolean field needs special handling
    need_assist_teacher = fields.Field(
        column_name='need_assist_teacher',
        attribute='need_assist_teacher',
        widget=BooleanWidget()
    )

    class Meta:
        model = Course
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('course_id', 'course_year', 'course_semester')
        fields = (
            'course_id',
            'course_year',
            'course_semester',
            'for_dept_id',
            'teaching_dept_id',
            'need_assist_teacher',
            'elective_type',
            'lab_type',
            'teaching_status',
        )
        export_order = fields

    def before_import_row(self, row, **kwargs):
        if 'lab_type' in row and row['lab_type'] == '':
            row['lab_type'] = None

    def get_instance(self, instance_loader, row):
        try:
            params = {
                'course_id__course_id': row['course_id'],
                'course_year': row['course_year'],
                'course_semester': row['course_semester'],
            }
            return self.get_queryset().get(**params)
        except Course.DoesNotExist:
            return None

    def after_import_instance(self, instance, new, **kwargs):
        if new and not instance.lab_type:
            instance.lab_type = 'NULL'