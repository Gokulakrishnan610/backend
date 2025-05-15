# import csv
# from django.core.management.base import BaseCommand
# from authentication.models import User
# from department.models import Department
# from teacher.models import Teacher
# from course.models import Course
# from rooms.models import Room

# class Command(BaseCommand):
#     help = 'Import CSV data into the database'

#     def handle(self, *args, **kwargs):
#         self.import_users()
#         self.import_departments()
#         self.import_teachers()
#         self.import_courses()
#         self.import_rooms()

#     def import_departments(self):
#         with open('data/departments.csv', newline='', encoding='utf-8-sig') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 # Ensure the HOD user exists
#                 hod_email = row['hod']
#                 try:
#                     hod_user = User.objects.get(email=hod_email)
#                 except User.DoesNotExist:
#                     # If user doesn't exist, create a default user
#                     hod_user = User.objects.create(
#                         email=hod_email,
#                         first_name='HOD',
#                         last_name=row['dept_name'],
#                         is_active=True,
#                         is_staff=True,
#                         is_superuser=False,
#                         password='pbkdf2_sha256$password_default',
#                         phone_number='',
#                         gender='M',
#                         user_type='teacher'
#                     )

#                 dept, created = Department.objects.get_or_create(
#                     dept_name=row['dept_name'],
#                     defaults={
#                         'date_established': row['date_established'],
#                         'contact_info': row['contact_info'],
#                         'hod': hod_user
#                     }
#                 )
#                 print(f"Department {'created' if created else 'exists'}: {dept.dept_name}")

#     def import_users(self):
#         with open('data/app_users.csv', newline='', encoding='utf-8-sig') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 # Split the name into first and last name
#                 name_parts = row['name'].split(' ', 1)
#                 first_name = name_parts[0]
#                 last_name = name_parts[1] if len(name_parts) > 1 else ''

#                 # Determine user type and other default values
#                 user_type = row['user_type'].lower()
#                 is_staff = user_type == 'teacher'
#                 is_superuser = False
                
#                 # Set default values for fields not in the CSV
#                 user, created = User.objects.get_or_create(
#                     email=row['email'],
#                     defaults={
#                         'first_name': first_name,
#                         'last_name': last_name,
#                         'password': row['password'],
#                         'is_active': True,
#                         'is_staff': is_staff,
#                         'is_superuser': is_superuser,
#                         'phone_number': '',  # Default value
#                         'gender': 'M',  # Default to Male
#                         'user_type': user_type
#                     }
#                 )
#                 print(f"User {'created' if created else 'exists'}: {user.email}")

#     def import_teachers(self):
#         with open('data/teachers.csv', newline='', encoding='utf-8-sig') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 # Ensure the teacher user exists
#                 teacher_user = User.objects.get(email=row['email'])
                
#                 # Find or create the department with default values
#                 dept, created = Department.objects.get_or_create(
#                     dept_name=row['department_name'],
#                     defaults={
#                         'date_established': '2000-01-01',  # Default date
#                         'contact_info': f'{row["department_name"].lower().replace(" ", "")}@rajalakshmi.edu.in',
#                         'hod': teacher_user  # Use the current teacher as HOD if not specified
#                     }
#                 )
                
#                 # Create or update teacher
#                 teacher, created = Teacher.objects.get_or_create(
#                     staff_code=row['staff_code'],
#                     dept=dept,
#                     teacher=teacher_user,
#                     defaults={
#                         'teacher_specialisation': row.get('specialization', ''),
#                         'teacher_working_hours': 21,  # Default from model
#                         'teacher_role': row['role'] if row['role'] in dict(Teacher.TEACHER_ROLES) else 'Professor'
#                     }
#                 )
#                 #print(f"Teacher {'created' if created else 'exists'}: {teacher_user.email}")

#     def import_courses(self):
#         with open('data/courses.csv', newline='', encoding='utf-8-sig') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 # Find or create the department with default values
#                 dept, _ = Department.objects.get_or_create(
#                     dept_name=row['department_name'],
#                     defaults={
#                         'date_established': '2000-01-01',  # Default date
#                         'contact_info': f'{row["department_name"].lower().replace(" ", "")}@rajalakshmi.edu.in',
#                         'hod': User.objects.first()  # Use the first user as HOD if not specified
#                     }
#                 )
                
#                 # Map course type to model choices
#                 course_type_map = {
#                     'Core': 'T',  # Assuming Core is a Theory course
#                     'Elective': 'T',  # Assuming Elective is a Theory course
#                     'Lab': 'L',
#                     'Theory': 'T',
#                     'LOT': 'T',  # Laboratory Oriented Theory
#                     'Laboratory': 'L',
#                     'Professional Elective': 'T',
#                     'Open Elective': 'T',
#                     'Others': 'T'
#                 }
                
#                 course, created = Course.objects.get_or_create(
#                     course_code=row['course_code'],
#                     department=dept,
#                     course_semester=int(float(row['semester'])),
#                     defaults={
#                         'course_name': row['course_name'],
#                         'regulation': row['regulation'],
#                         'course_type': course_type_map.get(row['category'], 'T'),
#                         'lecture_hours': int(float(row['lecture_hours'])),
#                         'tutorial_hours': int(float(row['tutorial_hours'])),
#                         'practical_hours': int(float(row['practical_hours'])),
#                         'credits': int(float(row['credits'])),
#                         'course_year': int(float(row['year']))
#                     }
#                 )
#                 print(f"Course {'created' if created else 'exists'}: {course.course_name}")

#     def import_rooms(self):
#         # Get or create a default department if no department is found
#         default_dept, _ = Department.objects.get_or_create(
#             dept_name='General',
#             defaults={
#                 'date_established': '2000-01-01',
#                 'contact_info': 'general@rajalakshmi.edu.in',
#                 'hod': User.objects.first()  # Use first user as HOD if not specified
#             }
#         )

#         with open('data/rooms.csv', newline='', encoding='utf-8-sig') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 # Try to get the department, fall back to default if not found
#                 try:
#                     dept = Department.objects.get(dept_name=row['maintained_by'])
#                 except Department.DoesNotExist:
#                     print(f"Warning: Department '{row['maintained_by']}' not found for room {row['room_number']}. Using default department.")
#                     dept = default_dept

#                 # Handle empty capacity values
#                 room_min_cap = row['room_min_cap'] if row['room_min_cap'] else 0
#                 room_max_cap = row['room_max_cap'] if row['room_max_cap'] else 0

#                 room, created = Room.objects.get_or_create(
#                     room_number=row['room_number'],
#                     defaults={
#                         'block': row['block'],
#                         'description': row['description'],
#                         'is_lab': row['is_lab'].lower() == 'true',
#                         'room_type': row['room_type'],
#                         'room_min_cap': float(room_min_cap),
#                         'room_max_cap': float(room_max_cap),
#                         'has_projector': row['has_projector'].lower() == 'true',
#                         'has_ac': row['has_ac'].lower() == 'true',
#                         'tech_level': row['tech_level'] if row['tech_level'] != 'None' else '',
#                         'maintained_by': dept
#                     }
#                 )
#                 print(f"Room {'created' if created else 'exists'}: {room.room_number} (Maintained by: {dept.dept_name})")

#     def get_user(self, email):
#         try:
#             return User.objects.get(email=email)
#         except User.DoesNotExist:
#             return None 