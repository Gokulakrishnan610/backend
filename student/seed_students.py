import os
import django
import csv
import threading
from queue import Queue
from django.utils import timezone
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UniversityApp.settings')
django.setup()

from student.models import Student
from authentication.models import User
from department.models import Department

class StudentCSVImporter:
    def __init__(self, csv_file_path, num_threads=4):
        self.csv_file_path = csv_file_path
        self.num_threads = num_threads
        self.queue = Queue()
        self.lock = threading.Lock()
        self.counter = 0
        self.total = 0
        self.errors = 0

    def process_row(self):
        while True:
            row = self.queue.get()
            if row is None:
                self.queue.task_done()
                break

            try:
                email = row['student_id__email']
                first_name = row['student_id__first_name']
                last_name = row['student_id__last_name']
                current_semester = int(row['current_semester'])
                year = int(row['year'])
                roll_no = row['roll_no']
                dept_name = row['dept']

                # Get or create department
                dept = Department.objects.get(dept_name=dept_name)

                # Create user
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'user_type': 'student',
                        'password': 'Changeme@123'  # Default password
                    }
                )

                if not created and user.user_type != 'student':
                    raise ValueError(f"User {email} exists but is not a student")

                # Calculate batch year
                current_year = timezone.now().year
                batch = current_year - year + 1  # Assuming year is the study year (1st year, 2nd year etc.)

                # Create student profile
                Student.objects.update_or_create(
                    student_id=user,
                    defaults={
                        'batch': batch,
                        'current_semester': current_semester,
                        'year': year,
                        'dept_id': dept,
                        'roll_no': roll_no,
                        'student_type': 'Mgmt',  # Default value
                        'degree_type': 'UG'      # Default value
                    }
                )

                with self.lock:
                    self.counter += 1
                    if self.counter % 50 == 0:
                        print(f"Processed {self.counter}/{self.total} records")

            except Exception as e:
                with self.lock:
                    self.errors += 1
                    print(f"Error processing {row.get('student_id__email', 'unknown')}: {str(e)}")

            self.queue.task_done()

    def import_students(self):
        # Read CSV and count total rows
        with open(self.csv_file_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.total = len(rows)

        print(f"Starting to import {self.total} students...")

        # Start worker threads
        threads = []
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.process_row)
            t.start()
            threads.append(t)

        # Add rows to queue
        for row in rows:
            self.queue.put(row)

        # Add poison pills to stop threads
        for _ in range(self.num_threads):
            self.queue.put(None)

        # Wait for all tasks to be processed
        self.queue.join()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        print(f"Finished importing students. Success: {self.counter}, Errors: {self.errors}")

if __name__ == "__main__":
    csv_file_path = "../csv/students.csv"  # Change this to your CSV file path
    importer = StudentCSVImporter(csv_file_path, num_threads=4)
    importer.import_students()