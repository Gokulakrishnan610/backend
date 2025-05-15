from django.db import models
from teacher.models import Teacher
from django.core.exceptions import ValidationError
from django.db.models import Count
from collections import Counter


# Create your models here.
class Slot(models.Model):
    SLOT_TYPES = [
        ('A', 'Slot A (8AM - 3PM)'),
        ('B', 'Slot B (10AM - 5PM)'),
        ('C', 'Slot C (12PM - 7PM)'),
    ]
    
    slot_name = models.CharField("Slot Name", max_length=20)
    slot_type = models.CharField("Slot Type", max_length=1, choices=SLOT_TYPES, default='A')
    slot_start_time = models.TimeField("Slot Start Time")
    slot_end_time = models.TimeField("Slot End Time")

    def __str__(self):
        return f"{self.slot_name} ({self.slot_start_time}-{self.slot_end_time})"
    
    def save(self, *args, **kwargs):
        # Auto-set times based on slot type if not manually specified
        if self.slot_type == 'A' and not (self.slot_start_time and self.slot_end_time):
            # Convert string time to TimeField in Django format
            from django.utils.dateparse import parse_time
            self.slot_start_time = parse_time('08:00:00')
            self.slot_end_time = parse_time('15:00:00')
        elif self.slot_type == 'B' and not (self.slot_start_time and self.slot_end_time):
            from django.utils.dateparse import parse_time
            self.slot_start_time = parse_time('10:00:00')
            self.slot_end_time = parse_time('17:00:00')
        elif self.slot_type == 'C' and not (self.slot_start_time and self.slot_end_time):
            from django.utils.dateparse import parse_time
            self.slot_start_time = parse_time('12:00:00')
            self.slot_end_time = parse_time('19:00:00')
        
        super().save(*args, **kwargs)

class TeacherSlotAssignment(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    # Update constraint to Saturday or Monday instead of weekend days
    RESTRICTED_DAYS = [0, 5]  # Monday and Saturday
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='slot_assignments')
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='teacher_assignments')
    day_of_week = models.IntegerField("Day of Week", choices=DAYS_OF_WEEK)
    
    class Meta:
        verbose_name = "Teacher Slot Assignment"
        verbose_name_plural = "Teacher Slot Assignments"
        ordering = ['day_of_week', 'slot__slot_start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'slot', 'day_of_week'],
                name='unique_teacher_slot_assignment'
            ),
            models.UniqueConstraint(
                fields=['teacher', 'day_of_week'],
                name='one_slot_per_teacher_per_day'
            )
        ]
    
    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK)[self.day_of_week]
        return f"{self.teacher} - {day_name} - {self.slot}"
    
    def clean(self):
        # Check total assignments constraint (max 5 days)
        if not self.pk:  # Only check for new assignments
            teacher_assignments = TeacherSlotAssignment.objects.filter(teacher=self.teacher)
            unique_days = teacher_assignments.values('day_of_week').distinct().count()
            
            if unique_days >= 5 and self.day_of_week not in teacher_assignments.values_list('day_of_week', flat=True):
                raise ValidationError(
                    f"This teacher already has assignments for 5 days. Maximum is 5 days per week."
                )
        
        # Check if the teacher already has this slot assigned for the same day
        existing_assignments = TeacherSlotAssignment.objects.filter(
            teacher=self.teacher,
            day_of_week=self.day_of_week
        ).exclude(pk=self.pk if self.pk else None)
        
        if existing_assignments.exists():
            raise ValidationError(
                f"This teacher already has a slot assigned for this day."
            )
        
        # Check Saturday or Monday constraint - teacher can only choose one of these days
        if self.day_of_week in self.RESTRICTED_DAYS:
            restricted_day_assignments = TeacherSlotAssignment.objects.filter(
                teacher=self.teacher,
                day_of_week__in=self.RESTRICTED_DAYS
            ).exclude(day_of_week=self.day_of_week).exclude(pk=self.pk if self.pk else None)
            
            if restricted_day_assignments.exists():
                restricted_day = dict(self.DAYS_OF_WEEK)[restricted_day_assignments.first().day_of_week]
                current_day = dict(self.DAYS_OF_WEEK)[self.day_of_week]
                
                raise ValidationError(
                    f"This teacher already has a slot assigned for {restricted_day}. "
                    f"Teachers can only choose one of these days: Monday or Saturday."
                )
        
        # Check slot type distribution constraint
        self.validate_slot_type_distribution()
        
        # Check department slot distribution constraint (33% per slot type)
        if self.teacher.dept_id:
            dept_id = self.teacher.dept_id.id
            total_dept_teachers = Teacher.objects.filter(dept_id=dept_id).count()
            
            if total_dept_teachers > 0:
                # Get count of teachers in this department assigned to this slot type on this day
                slot_type = self.slot.slot_type
                teachers_in_slot = TeacherSlotAssignment.objects.filter(
                    teacher__dept_id=dept_id,
                    day_of_week=self.day_of_week,
                    slot__slot_type=slot_type
                ).exclude(pk=self.pk if self.pk else None).values('teacher').distinct().count()
                
                # Calculate max teachers allowed (33% of department + 1 extra teacher)
                max_teachers_per_slot = int((total_dept_teachers * 0.33) + 0.5) + 1  # Adding 1 to allow one extra teacher
                
                if teachers_in_slot >= max_teachers_per_slot:
                    raise ValidationError(
                        f"Maximum number of teachers (33% + 1) from department {self.teacher.dept_id.dept_name} "
                        f"already assigned to slot type {slot_type} on {dict(self.DAYS_OF_WEEK)[self.day_of_week]}."
                    )
        
        return super().clean()
    
    def validate_slot_type_distribution(self):
        """
        Validate that a teacher's slot choices follow the required distribution format:
        Slot A, B, C must be chosen with a specific count totaling 5 days
        """
        # Get all assignments for this teacher including the current one
        current_assignments = list(TeacherSlotAssignment.objects.filter(
            teacher=self.teacher
        ).exclude(pk=self.pk if self.pk else None).values_list('slot__slot_type', flat=True))
        
        # Add the new assignment's slot type
        current_slot_type = self.slot.slot_type
        current_assignments.append(current_slot_type)
        
        # Count occurrence of each slot type
        slot_type_counts = Counter(current_assignments)
        total_assignments = len(current_assignments)
        
        # Don't need to check if less than 5 assignments since they can be added incrementally
        if total_assignments > 5:
            raise ValidationError("Teacher cannot have more than 5 slot assignments in total.")
        
        # When we reach 5 assignments, ensure we have a valid combination
        if total_assignments == 5:
            # Valid combinations should match one of these patterns:
            valid_combinations = [
                # Format: {A: count, B: count, C: count}
                {'A': 2, 'B': 2, 'C': 1},
                {'A': 1, 'B': 2, 'C': 2},
                {'A': 2, 'B': 1, 'C': 2}
            ]
            
            # Check if current distribution matches any valid combination
            if all(slot_type_counts.get(slot_type, 0) == count 
                  for valid_combo in valid_combinations 
                  for slot_type, count in valid_combo.items()):
                return True
            else:
                slot_a_count = slot_type_counts.get('A', 0)
                slot_b_count = slot_type_counts.get('B', 0)
                slot_c_count = slot_type_counts.get('C', 0)
                
                raise ValidationError(
                    f"Invalid slot distribution. Current distribution is: "
                    f"A: {slot_a_count}, B: {slot_b_count}, C: {slot_c_count}. "
                    f"Valid distributions for 5 days are: A-2/B-2/C-1, A-1/B-2/C-2, or A-2/B-1/C-2."
                )
        
        return True
    
    @classmethod
    def validate_teacher_assignments(cls, teacher):
        """
        Validates that a teacher's slot assignments follow the rules:
        - Maximum 5 days per week
        - Department distribution constraints
        - Slot type distribution constraint
        - Saturday/Monday constraint - only one of these days allowed
        """
        assignments = cls.objects.filter(teacher=teacher)
        
        # Check if teacher has more than 5 days assigned
        unique_days = assignments.values('day_of_week').distinct().count()
        if unique_days > 5:
            raise ValidationError(
                f"Teacher {teacher} has assignments for {unique_days} days. Maximum is 5 days per week."
            )
        
        # Check Saturday/Monday constraint
        restricted_days_assignments = assignments.filter(day_of_week__in=cls.RESTRICTED_DAYS)
        if restricted_days_assignments.count() > 1:
            raise ValidationError(
                f"Teacher {teacher} has assignments for multiple restricted days. "
                f"Only one of Monday or Saturday is allowed."
            )
        
        # Check slot type distribution constraint for 5 days
        if unique_days == 5:
            slot_types = assignments.values_list('slot__slot_type', flat=True)
            slot_type_counts = Counter(slot_types)
            
            valid_combinations = [
                {'A': 2, 'B': 2, 'C': 1},
                {'A': 1, 'B': 2, 'C': 2},
                {'A': 2, 'B': 1, 'C': 2}
            ]
            
            if not any(slot_type_counts.get(slot_type, 0) == count 
                      for valid_combo in valid_combinations 
                      for slot_type, count in valid_combo.items()):
                
                slot_a_count = slot_type_counts.get('A', 0)
                slot_b_count = slot_type_counts.get('B', 0)
                slot_c_count = slot_type_counts.get('C', 0)
                
                raise ValidationError(
                    f"Teacher {teacher} has invalid slot distribution. "
                    f"Current distribution is: A: {slot_a_count}, B: {slot_b_count}, C: {slot_c_count}. "
                    f"Valid distributions for 5 days are: A-2/B-2/C-1, A-1/B-2/C-2, or A-2/B-1/C-2."
                )
        
        return True