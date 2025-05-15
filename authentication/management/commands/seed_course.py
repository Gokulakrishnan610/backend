# authentication/management/commands/seed_course.py
from django.core.management.base import BaseCommand
import csv
from pathlib import Path
from courseMaster.models import CourseMaster
from course.models import Course
from department.models import Department
import os
from django.conf import settings

# Mappings for course type
COURSE_TYPE_MAPPING = {
    'Theory': 'T',
    'Laboratory': 'L',
    'LOT': 'LoT',
    'Lab and Theory': 'LoT',
    'Lab And Theory': 'LoT',
    'Open Elective': 'T',
}

# List of missing departments to be created
missing_depts = [
    "Robotics and Automation",
    "Another Missing Dept",
    # Add other missing departments here
]

class Command(BaseCommand):
    help = 'Seed the courses into the database'

    def handle(self, *args, **kwargs):
        # Create missing departments
        for name in missing_depts:
            Department.objects.get_or_create(dept_name=name)

        # Path to your CSV file
        csv_path = os.path.join(settings.BASE_DIR, 'csv', 'updated_courses.csv') 

        # Set to track skipped departments
        skipped_departments = set()

        # Process the CSV file
        with open(csv_path, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Skip invalid rows
                if not row['course_id'].strip() or not row['course_name'].strip():
                    print(f"[SKIP] Invalid row: {row}")
                    continue

                dept_name = row['course_dept_id'].strip()
                dept = Department.objects.filter(dept_name__iexact=dept_name).first()

                if not dept:
                    skipped_departments.add(dept_name)
                    print(f"[SKIP] Department not found: {dept_name}")
                    continue

                raw_type = row['course_type'].strip()
                course_type = COURSE_TYPE_MAPPING.get(raw_type, 'T')

                course_id_clean = row['course_id'].strip()

                # Create or update CourseMaster
                course_master, created = CourseMaster.objects.update_or_create(
                    course_id=course_id_clean,
                    defaults={
                        'course_name': row['course_name'].strip(),
                        'course_dept_id': dept,
                        'credits': int(row['credits']),
                        'lecture_hours': int(row['lecture_hours']),
                        'practical_hours': int(row['practical_hours']),
                        'tutorial_hours': int(row['tutorial_hours']),
                        'regulation': str(row['regulation']).strip().rstrip('.0'),
                        'course_type': course_type,
                        'is_zero_credit_course': int(row['credits']) == 0,
                    }
                )
                print(f"[{'CREATED' if created else 'UPDATED'}] CourseMaster: {course_master.course_id}")

                # Determine elective type
                elective_type = 'OE' if 'Open Elective' in raw_type else 'NE'

                # Determine lab type
                if course_type == 'L':
                    lab_type = 'TL'
                elif course_type == 'T':
                    lab_type = 'NULL'
                else:
                    lab_type = 'TL'

                # Create a Course entry pointing to this CourseMaster
                course_obj, created_course = Course.objects.update_or_create(
                    course_id=course_master,
                    course_year=1,  # You can modify or infer year/semester if needed
                    course_semester=1,
                    defaults={
                        'for_dept_id': dept,
                        'teaching_dept_id': dept,
                        'elective_type': elective_type,
                        'lab_type': lab_type,
                        'teaching_status': 'active',
                        'need_assist_teacher': False,
                    }
                )
                print(f"[{'CREATED' if created_course else 'UPDATED'}] Course: {course_obj}")

        # After the loop:
        print(f"Skipped departments ({len(skipped_departments)}): {skipped_departments}")
