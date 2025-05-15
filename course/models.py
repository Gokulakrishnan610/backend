from django.db import models

# Create your models here.
class Course(models.Model):
    COURSE_TYPE = [
        ('T', 'Theory'),
        ('L', 'Lab'),
        ('LoT', 'Lab And Theory'),
    ]
    ELECTIVE_TYPE = [
        ('NE', 'Non-Elective'),
        ('PE', 'Professional Elective'),
        ('OE', 'Open Elective'),
    ]
    LAB_TYPE = [
        ('NULL', 'NULL'),
        ('TL', 'Technical Lab'),
        ('NTL', 'Non-Technical Lab')
    ]
    TEACHING_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending')
    ]

    course_id = models.ForeignKey("courseMaster.CourseMaster", on_delete=models.CASCADE)
    course_year = models.IntegerField("Course Year", default=1)
    course_semester = models.IntegerField("Course Semester", default=1)
    # is_zero_credit_course = models.BooleanField("Is Zero Credit Course?", default=False)
    # lecture_hours = models.IntegerField("Lecture Hours", default=0)
    # practical_hours = models.IntegerField("Practical Hours", default=0)
    # tutorial_hours = models.IntegerField("Tutorial Hours", default=0)
    # credits = models.IntegerField("Course Credit", default=0)
    for_dept_id = models.ForeignKey("department.Department", on_delete=models.SET_NULL, null=True, related_name="courses_for_dept")
    teaching_dept_id = models.ForeignKey("department.Department", on_delete=models.SET_NULL, null=True, related_name="courses_taught_by_dept")
    need_assist_teacher = models.BooleanField("Assist teacher?", default=False)
    # regulation = models.CharField("Regulation", max_length=50)
    # course_type = models.CharField("Course Type", max_length=50, default='T', choices=COURSE_TYPE)
    elective_type = models.CharField("Elective Type", max_length=50, default='NE', choices=ELECTIVE_TYPE)
    lab_type = models.CharField("Lab Type", max_length=50, default='NULL', choices=LAB_TYPE, null=True, blank=True)
    # no_of_students = models.IntegerField("No. of students", default=0)
    teaching_status = models.CharField("Teaching Status", max_length=50, default='active', choices=TEACHING_STATUS)

    def __str__(self):
        return f"{self.course_id.course_id} - {self.course_id.course_name} (Year: {self.course_year}, Sem: {self.course_semester})"

class CourseResourceAllocation(models.Model):
    ALLOCATION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resource_allocations')
    original_dept_id = models.ForeignKey("department.Department", on_delete=models.CASCADE, related_name='original_dept_allocations')
    teaching_dept_id = models.ForeignKey("department.Department", on_delete=models.CASCADE, related_name='teaching_dept_allocations')
    allocation_reason = models.TextField("Allocation Reason", blank=True)
    allocation_date = models.DateField("Allocation Date", auto_now_add=True)
    status = models.CharField("Status", max_length=50, choices=ALLOCATION_STATUS, default='pending')
    
    def __str__(self):
        return f"{self.course_id} - From: {self.original_dept_id} To: {self.teaching_dept_id}"

class CourseSlotPreference(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='slot_preferences')
    slot_id = models.ForeignKey("slot.Slot", on_delete=models.CASCADE)
    preference_level = models.IntegerField("Preference Level", default=0)
    
    def __str__(self):
        return f"{self.course_id} - Slot: {self.slot_id} (Level: {self.preference_level})"

class CourseRoomPreference(models.Model):
    ROOM_TYPE = [
        ('GENERAL', 'General'),
        ('TL', 'Technical Lab'),
        ('NTL', 'Non-Technical Lab')
    ]
    TECH_LEVEL = [
        ('None', 'None'),
        ('Basic', 'Basic'),
        ('Advanced', 'Advanced'),
        ('High-tech', 'High-tech')
    ]
    LAB_TYPE = [
        ('low-end', 'Low-End - For programming and basic coding'),
        ('mid-end', 'Mid-End - For OS and computation-intensive subjects'),
        ('high-end', 'High-End - For ML, NLP, and resource-intensive subjects')
    ]
    
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='room_preferences')
    room_id = models.ForeignKey("rooms.Room", on_delete=models.CASCADE, null=True, blank=True)
    preference_level = models.IntegerField("Preference Level", default=0)
    preferred_for = models.CharField("Preferred For", max_length=50, choices=ROOM_TYPE, default='GENERAL')
    tech_level_preference = models.CharField("Tech Level Preference", max_length=50, choices=TECH_LEVEL, default='None')
    lab_type = models.CharField("Lab Type", max_length=50, choices=LAB_TYPE, null=True, blank=True)
    lab_description = models.TextField("Lab Description", null=True, blank=True)
    
    def __str__(self):
        return f"{self.course_id} - Room: {self.room_id} (Level: {self.preference_level})"

