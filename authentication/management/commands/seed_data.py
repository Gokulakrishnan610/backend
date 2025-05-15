# import random
# import datetime
# from django.core.management.base import BaseCommand
# from django.db import transaction
# from django.utils import timezone
# from faker import Faker

# from authentication.models import User
# from department.models import Department
# from teacher.models import Teacher
# from student.models import Student
# from course.models import Course
# from rooms.models import Room
# from slot.models import Slot
# from teacherCourse.models import TeacherCourse
# from studentCourse.models import StudentCourse
# from courseMaster.models import CourseMaster

# class Command(BaseCommand):
#     help = 'Seed database with fake data for all models'

#     def __init__(self, *args, **kwargs):
#         super(Command, self).__init__(*args, **kwargs)
#         self.fake = Faker()

#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--clear',
#             action='store_true',
#             help='Clear existing data before seeding',
#         )
#         parser.add_argument(
#             '--skip-csv',
#             action='store_true',
#             help='Skip importing CSV data',
#         )

#     def handle(self, *args, **kwargs):
#         clear = kwargs.get('clear', False)
#         skip_csv = kwargs.get('skip_csv', False)
        
#         if clear:
#             self.clear_data()
#             self.stdout.write(self.style.SUCCESS('All data cleared successfully'))
        
#         # First, seed real data from CSV files
#         if not skip_csv:
#             self.stdout.write(self.style.SUCCESS('Seeding real data from CSV files...'))
#             call_command = self.call_command
#             try:
#                 from django.core.management import call_command
#                 call_command('import_data')
#                 self.stdout.write(self.style.SUCCESS('CSV data imported successfully'))
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f'Error importing CSV data: {e}'))
#                 self.stdout.write(self.style.WARNING('Continuing with fake data generation...'))
        
#         # Check if we have departments
#         if not Department.objects.exists():
#             self.seed_departments(5)
        
#         # Now seed the remaining models with fake data (limited number)
#         self.seed_additional_users(10)
#         self.seed_students(10)
#         self.seed_course_master(5)
#         self.seed_slots()
#         self.seed_teacher_courses(10)
#         self.seed_student_courses(20)
        
#         self.stdout.write(self.style.SUCCESS('Database seeded successfully'))

#     def clear_data(self):
#         """Clear all data from the database."""
#         with transaction.atomic():
#             self.stdout.write("Deleting StudentCourse records...")
#             StudentCourse.objects.all().delete()
            
#             self.stdout.write("Deleting TeacherCourse records...")
#             TeacherCourse.objects.all().delete()
            
#             self.stdout.write("Deleting Slot records...")
#             Slot.objects.all().delete()
            
#             self.stdout.write("Deleting Student records...")
#             Student.objects.all().delete()
            
#             self.stdout.write("Deleting CourseMaster records...")
#             CourseMaster.objects.all().delete()
#             # Don't delete imported data (Users, Teachers, Courses, Departments, Rooms)
    
#     def seed_departments(self, count):
#         """Create basic departments if none exist."""
#         self.stdout.write(self.style.SUCCESS(f'Creating {count} departments...'))
        
#         # Create a superuser to be HOD if none exists
#         admin_user = None
#         try:
#             admin_user = User.objects.filter(is_superuser=True).first()
#             if not admin_user:
#                 admin_user = User.objects.create(
#                     email="admin@university.edu",
#                     first_name="Admin",
#                     last_name="User",
#                     password='pbkdf2_sha256$600000$cHw1HWXZpIecfBRLvuWwpC$Nf+qBR1/iY8UDivz23nCrWIUJVpHjN3Nf+qI5ITQHu8=',  # "password123"
#                     is_active=True,
#                     is_staff=True,
#                     is_superuser=True,
#                     phone_number=self.fake.phone_number(),
#                     gender='M',
#                     user_type='teacher'
#                 )
#                 self.stdout.write(f'Created admin user: {admin_user.email}')
#         except Exception as e:
#             self.stdout.write(self.style.ERROR(f'Error creating admin user: {e}'))
            
#         # Create some departments
#         department_names = [
#             "Computer Science", 
#             "Electrical Engineering", 
#             "Mechanical Engineering",
#             "Civil Engineering",
#             "Information Technology",
#             "Mathematics",
#             "Physics",
#             "Chemistry"
#         ]
        
#         created_count = 0
#         with transaction.atomic():
#             for i in range(min(count, len(department_names))):
#                 dept_name = department_names[i]
#                 dept, created = Department.objects.get_or_create(
#                     dept_name=dept_name,
#                     defaults={
#                         'date_established': timezone.now().date() - datetime.timedelta(days=365*5),
#                         'contact_info': f"{dept_name.lower().replace(' ', '')}@university.edu",
#                         'hod_id': admin_user
#                     }
#                 )
#                 if created:
#                     created_count += 1
                    
#         self.stdout.write(f'Created {created_count} departments')
            
#     def seed_additional_users(self, count):
#         """Create additional fake users if needed."""
#         self.stdout.write(self.style.SUCCESS(f'Creating up to {count} additional users...'))
        
#         existing_count = User.objects.count()
#         if existing_count >= 50:  # If we already have enough users from CSV import
#             self.stdout.write(self.style.SUCCESS(f'Skipping additional users - {existing_count} users already exist'))
#             return
        
#         created_count = 0    
#         with transaction.atomic():
#             for _ in range(count):
#                 gender = random.choice(['M', 'F'])
#                 user_type = random.choice(['student', 'teacher'])
                
#                 user = User.objects.create(
#                     email=self.fake.email(),
#                     first_name=self.fake.first_name_male() if gender == 'M' else self.fake.first_name_female(),
#                     last_name=self.fake.last_name(),
#                     password='pbkdf2_sha256$600000$cHw1HWXZpIecfBRLvuWwpC$Nf+qBR1/iY8UDivz23nCrWIUJVpHjN3Nf+qI5ITQHu8=',  # "password123"
#                     is_active=True,
#                     is_staff=user_type == 'teacher',
#                     is_superuser=False,
#                     phone_number=self.fake.phone_number(),
#                     gender=gender,
#                     user_type=user_type
#                 )
#                 created_count += 1
                
#         self.stdout.write(f'Created {created_count} additional users')
                
#     def seed_students(self, count):
#         """Create fake students."""
#         self.stdout.write(self.style.SUCCESS(f'Creating up to {count} students...'))
        
#         # Get all users of type 'student' who don't have a student profile
#         student_users = list(User.objects.filter(
#             user_type='student',
#             student_profile__isnull=True
#         ))
        
#         if not student_users:
#             self.stdout.write(self.style.WARNING('No student users without profiles found. Creating some...'))
#             # Create student users explicitly
#             for i in range(count):
#                 gender = random.choice(['M', 'F'])
#                 user = User.objects.create(
#                     email=f"student{i}@university.edu",
#                     first_name=self.fake.first_name_male() if gender == 'M' else self.fake.first_name_female(),
#                     last_name=self.fake.last_name(),
#                     password='pbkdf2_sha256$600000$cHw1HWXZpIecfBRLvuWwpC$Nf+qBR1/iY8UDivz23nCrWIUJVpHjN3Nf+qI5ITQHu8=',  # "password123"
#                     is_active=True,
#                     is_staff=False,
#                     is_superuser=False,
#                     phone_number=self.fake.phone_number(),
#                     gender=gender,
#                     user_type='student'
#                 )
#                 student_users.append(user)
#             self.stdout.write(f'Created {count} student users')
        
#         # Get all departments
#         departments = list(Department.objects.all())
#         if not departments:
#             self.stdout.write(self.style.ERROR('No departments found. Cannot create students.'))
#             return
            
#         created_count = 0
#         with transaction.atomic():
#             for i in range(min(count, len(student_users))):
#                 student_user = student_users[i]
                
#                 current_year = datetime.datetime.now().year
#                 batch = random.randint(current_year - 4, current_year)
#                 current_semester = random.randint(1, 8)
#                 year = (current_semester + 1) // 2  # Convert semester to year
                
#                 student = Student.objects.create(
#                     student_id=student_user,
#                     batch=batch,
#                     current_semester=current_semester,
#                     year=year,
#                     dept_id=random.choice(departments),
#                     roll_no=f"{batch % 100}{random.randint(1000, 9999)}",
#                     student_type=random.choice(['Mgmt', 'Govt']),
#                     degree_type=random.choice(['UG', 'PG'])
#                 )
#                 created_count += 1
                
#         self.stdout.write(f'Created {created_count} students')
                
#     def seed_course_master(self, count):
#         """Create fake course master entries."""
#         self.stdout.write(self.style.SUCCESS(f'Creating {count} course master entries...'))
        
#         # Get all departments
#         departments = list(Department.objects.all())
#         if not departments:
#             self.stdout.write(self.style.ERROR('No departments found. Cannot create course master entries.'))
#             return
            
#         # Check existing courses to avoid duplication
#         existing_course_ids = set()  # We'll maintain our own set to avoid duplicates
        
#         created_count = 0
#         with transaction.atomic():
#             for _ in range(count):
#                 course_id = f"CM{random.randint(1000, 9999)}"
#                 while course_id in existing_course_ids:
#                     course_id = f"CM{random.randint(1000, 9999)}"
                
#                 course = CourseMaster.objects.create(
#                     course_id=course_id,
#                     course_name=self.fake.sentence(nb_words=4).strip('.'),
#                     course_dept_id=random.choice(departments)
#                 )
#                 created_count += 1
#                 existing_course_ids.add(course_id)
                
#         self.stdout.write(f'Created {created_count} course master entries')
        
#         # After creating course masters, let's create some courses
#         self.seed_courses(count * 2)
    
#     def seed_courses(self, count):
#         """Create fake courses based on course master entries."""
#         self.stdout.write(self.style.SUCCESS(f'Creating {count} courses...'))
        
#         # Get all course masters
#         course_masters = list(CourseMaster.objects.all())
#         if not course_masters:
#             self.stdout.write(self.style.ERROR('No course masters found. Cannot create courses.'))
#             return
            
#         # Get all departments
#         departments = list(Department.objects.all())
#         if not departments:
#             self.stdout.write(self.style.ERROR('No departments found. Cannot create courses.'))
#             return
            
#         created_count = 0
#         with transaction.atomic():
#             for _ in range(count):
#                 course_master = random.choice(course_masters)
                
#                 # Get two random departments (one for teaching, one for students)
#                 dept1, dept2 = random.sample(departments, min(2, len(departments)))
                
#                 course = Course.objects.create(
#                     course_id=course_master,
#                     course_year=random.randint(1, 4),
#                     course_semester=random.randint(1, 8),
#                     is_zero_credit_course=random.choice([True, False]),
#                     lecture_hours=random.randint(0, 3),
#                     practical_hours=random.randint(0, 3),
#                     tutorial_hours=random.randint(0, 1),
#                     credits=random.randint(1, 4),
#                     for_dept_id=dept1,
#                     teaching_dept_id=dept2,
#                     need_assist_teacher=random.choice([True, False]),
#                     regulation=f"REG-{random.randint(2018, 2024)}",
#                     course_type=random.choice(['T', 'L', 'LoT']),
#                     elective_type=random.choice(['NE', 'PE', 'OE']),
#                     lab_type='TL' if random.choice([True, False]) else 'NTL',
#                     no_of_students=random.randint(30, 120),
#                     teaching_status=random.choice(['active', 'inactive', 'pending'])
#                 )
#                 created_count += 1
                
#         self.stdout.write(f'Created {created_count} courses')
                
#     def seed_slots(self):
#         """Create time slots for classes."""
#         self.stdout.write(self.style.SUCCESS('Creating time slots...'))
        
#         # Check if slots already exist
#         if Slot.objects.exists():
#             self.stdout.write(self.style.WARNING('Slots already exist. Skipping.'))
#             return
            
#         # Create standard slots
#         slots = [
#             ('A', '08:30:00', '09:20:00'),
#             ('B', '09:20:00', '10:10:00'),
#             ('C', '10:10:00', '11:00:00'),
#             ('D', '11:15:00', '12:05:00'),
#             ('E', '12:05:00', '12:55:00'),
#             ('F', '01:40:00', '02:30:00'),
#             ('G', '02:30:00', '03:20:00'),
#             ('H', '03:20:00', '04:10:00'),
#             ('I', '04:10:00', '05:00:00')
#         ]
        
#         created_count = 0
#         with transaction.atomic():
#             for slot_name, start_time, end_time in slots:
#                 slot = Slot.objects.create(
#                     slot_name=slot_name,
#                     slot_start_time=start_time,
#                     slot_end_time=end_time
#                 )
#                 created_count += 1
                
#         self.stdout.write(f'Created {created_count} time slots')
                
#     def seed_teacher_courses(self, count):
#         """Assign teachers to courses."""
#         self.stdout.write(self.style.SUCCESS(f'Assigning up to {count} teacher-course relationships...'))
        
#         teachers = list(Teacher.objects.all())
#         courses = list(Course.objects.all())
        
#         if not teachers:
#             self.stdout.write(self.style.WARNING('No teachers found. Creating some...'))
#             self.seed_teachers(5)
#             teachers = list(Teacher.objects.all())
            
#         if not courses:
#             self.stdout.write(self.style.WARNING('No courses found. Seed courses first!'))
#             return
            
#         if not teachers or not courses:
#             self.stdout.write(self.style.ERROR('No teachers or courses found. Cannot create teacher-course relationships.'))
#             return
            
#         current_year = datetime.datetime.now().year
        
#         created_count = 0
#         error_count = 0
#         with transaction.atomic():
#             # First group teachers by department
#             teachers_by_dept = {}
#             for teacher in teachers:
#                 if teacher.dept_id:
#                     dept_id = teacher.dept_id.id
#                     if dept_id not in teachers_by_dept:
#                         teachers_by_dept[dept_id] = []
#                     teachers_by_dept[dept_id].append(teacher)
            
#             # Then group courses by teaching department
#             courses_by_dept = {}
#             for course in courses:
#                 if course.teaching_dept_id:
#                     dept_id = course.teaching_dept_id.id
#                     if dept_id not in courses_by_dept:
#                         courses_by_dept[dept_id] = []
#                     courses_by_dept[dept_id].append(course)
            
#             # Now try to create valid teacher-course assignments
#             attempts = 0
#             while created_count < count and attempts < count * 3:
#                 attempts += 1
                
#                 # Find departments that have both teachers and courses
#                 common_depts = set(teachers_by_dept.keys()).intersection(set(courses_by_dept.keys()))
#                 if not common_depts:
#                     self.stdout.write(self.style.WARNING('No matching departments between teachers and courses'))
#                     break
                
#                 # Pick a random department with both teachers and courses
#                 dept_id = random.choice(list(common_depts))
#                 dept_teachers = teachers_by_dept[dept_id]
#                 dept_courses = courses_by_dept[dept_id]
                
#                 # Pick a random teacher and course from the same department
#                 teacher = random.choice(dept_teachers)
#                 course = random.choice(dept_courses)
#                 semester = random.choice([1, 2, 3, 4, 5, 6, 7, 8])
                
#                 # Skip if the relationship already exists
#                 if TeacherCourse.objects.filter(teacher_id=teacher, course_id=course, semester=semester).exists():
#                     continue
                
#                 try:
#                     TeacherCourse.objects.create(
#                         teacher_id=teacher,
#                         course_id=course,
#                         student_count=random.randint(10, 60),
#                         academic_year=current_year,
#                         semester=semester
#                     )
#                     created_count += 1
#                 except Exception as e:
#                     error_count += 1
#                     if error_count < 3:  # Only show first few errors
#                         self.stdout.write(self.style.ERROR(f'Error creating teacher-course: {e}'))
                
#         self.stdout.write(f'Created {created_count} teacher-course relationships (Errors: {error_count})')
    
#     def seed_teachers(self, count):
#         """Create fake teachers."""
#         self.stdout.write(self.style.SUCCESS(f'Creating up to {count} teachers...'))
        
#         # Get all users of type 'teacher' who don't have a teacher profile
#         teacher_users = User.objects.filter(
#             user_type='teacher',
#             teacher_profile__isnull=True
#         )
        
#         if not teacher_users.exists():
#             self.stdout.write(self.style.WARNING('No teacher users without profiles found. Creating some...'))
#             for _ in range(5):
#                 User.objects.create(
#                     email=f"teacher{_}@university.edu",
#                     first_name=self.fake.first_name(),
#                     last_name=self.fake.last_name(),
#                     password='pbkdf2_sha256$600000$cHw1HWXZpIecfBRLvuWwpC$Nf+qBR1/iY8UDivz23nCrWIUJVpHjN3Nf+qI5ITQHu8=',  # "password123"
#                     is_active=True,
#                     is_staff=True,
#                     is_superuser=False,
#                     phone_number=self.fake.phone_number(),
#                     gender=random.choice(['M', 'F']),
#                     user_type='teacher'
#                 )
#             teacher_users = User.objects.filter(user_type='teacher', teacher_profile__isnull=True)
        
#         # Get all departments
#         departments = list(Department.objects.all())
#         if not departments:
#             self.stdout.write(self.style.ERROR('No departments found. Cannot create teachers.'))
#             return
            
#         created_count = 0
#         with transaction.atomic():
#             for _ in range(min(count, teacher_users.count())):
#                 teacher_user = teacher_users[_]
                
#                 teacher = Teacher.objects.create(
#                     teacher_id=teacher_user,
#                     dept_id=random.choice(departments),
#                     staff_code=f"STAFF{random.randint(1000, 9999)}",
#                     teacher_role=random.choice(['Professor', 'Asst. Professor', 'DC']),
#                     teacher_specialisation=self.fake.sentence(nb_words=3),
#                     teacher_working_hours=random.randint(15, 25)
#                 )
#                 created_count += 1
                
#         self.stdout.write(f'Created {created_count} teachers')
                
#     def seed_student_courses(self, count):
#         """Enroll students in courses."""
#         self.stdout.write(self.style.SUCCESS(f'Enrolling up to {count} student-course relationships...'))
        
#         students = list(Student.objects.all())
#         courses = list(Course.objects.all())
        
#         if not students or not courses:
#             self.stdout.write(self.style.ERROR('No students or courses found. Cannot create student-course relationships.'))
#             return
            
#         created_count = 0
#         with transaction.atomic():
#             for _ in range(count*2):  # Try more times to get the desired count
#                 if created_count >= count:
#                     break
                    
#                 student = random.choice(students)
                
#                 # Filter courses by student's semester
#                 relevant_courses = [c for c in courses if c.course_semester == student.current_semester]
#                 if not relevant_courses:
#                     relevant_courses = courses  # Fallback to all courses
                    
#                 course = random.choice(relevant_courses)
                
#                 # Skip if the relationship already exists
#                 if StudentCourse.objects.filter(student_id=student, course_id=course).exists():
#                     continue
                
#                 StudentCourse.objects.create(
#                     student_id=student,
#                     course_id=course
#                 )
#                 created_count += 1
                
#         self.stdout.write(f'Created {created_count} student-course enrollments')
                
#     def call_command(self, command, *args, **kwargs):
#         """Helper method to call a management command."""
#         from django.core.management import call_command
#         call_command(command, *args, **kwargs) 