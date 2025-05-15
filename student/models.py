# models.py
from django.db import models
from django.core.exceptions import ValidationError

class Student(models.Model):
    STUDENT_TYPE = [
        ('Mgmt', 'Management'),
        ('Govt', 'Government'),
    ]
    DEGREE_TYPE = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate')
    ]
    
    student_id = models.ForeignKey('authentication.User', on_delete=models.CASCADE, related_name='student_profile', null=True)
    batch = models.IntegerField('Batch', default=0)
    current_semester = models.IntegerField('Semester', default=1)
    year = models.IntegerField('Year', default=0)
    dept_id = models.ForeignKey('department.Department', on_delete=models.SET_NULL, null=True, related_name='department_students')
    roll_no = models.CharField('Roll No', max_length=50, blank=True, null=True)
    student_type = models.CharField("Student Type", max_length=50, default='Mgmt', choices=STUDENT_TYPE)
    degree_type = models.CharField("Degree Type", max_length=50, default='UG', choices=DEGREE_TYPE)

    def __str__(self):
        name = self.student_id.get_full_name() if self.student_id else "Unknown"
        return f"{name} (Batch: {self.batch})"

    def clean(self):
        if self.student_id and not self.student_id.user_type == 'student':
            raise ValidationError("Associated user must be of type 'student'")
        if not (1 <= self.current_semester <= 10):
            raise ValidationError("Semester must be between 1 and 10")
        return super().clean()
