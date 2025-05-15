from django.db import models
from timetable.models import Timetable
from student.models import Student
from teacher.models import Teacher

class AttendanceSession(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Rescheduled', 'Rescheduled'),
    ]
    
    timetable_slot = models.ForeignKey(Timetable, on_delete=models.CASCADE)
    date = models.DateField()  # Actual date when this class occurred
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    cancel_reason = models.TextField(blank=True, null=True)
    substitute_teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='substituted_sessions'
    )
    conducted_by = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE, 
        related_name='conducted_sessions'
    )
    
    class Meta:
        db_table = 'attendance_session'
        unique_together = (('timetable_slot', 'date'),)
    
    def __str__(self):
        return f"{self.timetable_slot} - {self.date} - {self.status}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Excused', 'Excused'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    timetable_slot = models.ForeignKey(Timetable, on_delete=models.CASCADE)
    date = models.DateField()  # Actual date of the class session
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True, null=True)
    time_marked = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance'
        unique_together = (('student', 'timetable_slot', 'date'),)  # One attendance record per student per class
    
    def __str__(self):
        return f"{self.student} - {self.timetable_slot} - {self.date} - {self.status}"
    
    @property
    def is_present(self):
        return self.status == 'Present'
    
    @property
    def session(self):
        """Get the corresponding session for this attendance record"""
        try:
            return AttendanceSession.objects.get(timetable_slot=self.timetable_slot, date=self.date)
        except AttendanceSession.DoesNotExist:
            return None
