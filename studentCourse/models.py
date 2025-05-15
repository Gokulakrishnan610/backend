from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.
class StudentCourse(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    student_id = models.ForeignKey("student.Student", on_delete=models.CASCADE, null=True)
    course_id = models.ForeignKey("course.Course", on_delete=models.CASCADE, null=True)
    teacher_id = models.ForeignKey("teacher.Teacher", on_delete=models.CASCADE, null=True)
    slot_id = models.ForeignKey("slot.Slot", on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student_id', 'course_id']  # A student can only select a course once

    def clean(self):
        # Check if the teacher is assigned to this course
        if self.teacher_id and self.course_id:
            teacher_course = self.teacher_id.teachercourse_set.filter(course_id=self.course_id).first()
            if not teacher_course:
                raise ValidationError("Selected teacher is not assigned to this course")
        
        # Check for time slot conflicts
        if self.student_id and self.slot_id:
            conflicts = StudentCourse.objects.filter(
                student_id=self.student_id,
                slot_id=self.slot_id,
                status='approved'
            ).exclude(id=self.id)
            if conflicts.exists():
                raise ValidationError("Time slot conflicts with another course")

    def __str__(self):
        student_str = str(self.student_id) if self.student_id else "Unknown Student"
        course_str = str(self.course_id) if self.course_id else "Unknown Course"
        return f"{student_str} - {course_str}"

class StudentCoursePreference(models.Model):
    student_course = models.ForeignKey(StudentCourse, on_delete=models.CASCADE, related_name='preferences')
    teacher_id = models.ForeignKey("teacher.Teacher", on_delete=models.CASCADE)
    preference_order = models.IntegerField()  # Lower number means higher preference
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student_course', 'teacher_id']
        ordering = ['preference_order']

    def clean(self):
        # Verify teacher teaches this course
        if not self.teacher_id.teachercourse_set.filter(course_id=self.student_course.course_id).exists():
            raise ValidationError("Selected teacher does not teach this course")

    def __str__(self):
        return f"{self.student_course} - Teacher: {self.teacher_id} (Preference: {self.preference_order})"