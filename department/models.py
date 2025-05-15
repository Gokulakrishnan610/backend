from django.db import models
from django.core.exceptions import ValidationError

class Department(models.Model):
    dept_name = models.CharField("Department", max_length=100, blank=False)
    date_established = models.DateField("Est.", blank=True, null=True)
    contact_info = models.CharField("Contact Details", max_length=255, blank=True)
    hod_id = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='department_hod')

    def __str__(self):
        return self.dept_name

    def clean(self):
        self.dept_name = self.dept_name.title()
        if self.hod_id and self.hod_id.user_type != 'teacher':
            raise ValidationError("Only teachers can be assigned as HOD")
        return super().clean()