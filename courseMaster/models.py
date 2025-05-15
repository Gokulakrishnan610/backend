from django.db import models

# Create your models here.
class CourseMaster(models.Model):
    COURSE_TYPE = [
        ('T', 'Theory'),
        ('L', 'Lab'),
        ('LoT', 'Lab And Theory'),
    ]

    DEGREE_NAME_TYPE = [
        ('BE', 'Bachelor of Engineering'),
        ('BTECH', 'Bachelor of Technology'),
        ('ME', 'Master of Engineering'),
        ('MTECH', 'Master of Technology'),
        ('MBA', 'Master of Business Administration'),
        ('MCA', 'Master of Computer Applications'),
    ] 
    course_id = models.CharField("Course ID", max_length=50, blank=False)
    course_name = models.CharField("Course Name", max_length=255, blank=False)
    course_dept_id = models.ForeignKey("department.Department", on_delete=models.SET_NULL, null=True, related_name='course_master')
    is_zero_credit_course = models.BooleanField("Is Zero Credit Course?", default=False)
    lecture_hours = models.IntegerField("Lecture Hours", default=0)
    practical_hours = models.IntegerField("Practical Hours", default=0)
    tutorial_hours = models.IntegerField("Tutorial Hours", default=0)
    credits = models.IntegerField("Course Credit", default=0)
    regulation = models.CharField("Regulation", max_length=50, default=0)
    course_type = models.CharField("Course Type", max_length=50, default='T', choices=COURSE_TYPE)
    is_zero_credit_course = models.BooleanField("Is Zero Credit Course?", default=False)
    degree_type= models.CharField("Degree Type", default='BE', choices=DEGREE_NAME_TYPE)

    # degree_name = models.CharField('Degree Name', max_length=50, null=True,choices=DEGREE_NAME_TYPE)
    def __str__(self):
        dept_name = self.course_dept_id.dept_name if self.course_dept_id else "No Department"
        return f'{self.course_id}-{self.course_name}-{dept_name}'