# courseMaster/resources.py
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, BooleanWidget
from .models import CourseMaster
from department.models import Department

class CourseMasterResource(resources.ModelResource):
    course_dept_id = fields.Field(
        column_name='course_dept_id',
        attribute='course_dept_id',
        widget=ForeignKeyWidget(Department, 'dept_name')
    )
    
    is_zero_credit_course = fields.Field(
        column_name='is_zero_credit_course',
        attribute='is_zero_credit_course',
        widget=BooleanWidget()
    )

    class Meta:
        model = CourseMaster
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('course_id',)
        fields = (
            'course_id',
            'course_name',
            'course_dept_id',
            'is_zero_credit_course',
            'lecture_hours',
            'practical_hours',
            'tutorial_hours',
            'credits',
            'regulation',
            'course_type',
        )
        export_order = fields

    def before_import_row(self, row, **kwargs):
        # Convert empty string regulation to None or empty string
        if 'regulation' in row and row['regulation'].strip() == '':
            row['regulation'] = ''

        # Handle potential nulls for hours
        for field in ['lecture_hours', 'practical_hours', 'tutorial_hours', 'credits']:
            if field in row and row[field] == '':
                row[field] = 0

    def get_instance(self, instance_loader, row):
        """
        Identify CourseMaster instance by course_id.
        """
        try:
            return self.get_queryset().get(course_id=row['course_id'])
        except CourseMaster.DoesNotExist:
            return None

    def after_import_instance(self, instance, new, **kwargs):
        """
        Set default course_type if missing or incorrect
        """
        if new and instance.course_type not in dict(CourseMaster.COURSE_TYPE).keys():
            instance.course_type = 'T'
            instance.save()
