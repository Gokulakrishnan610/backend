import csv
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from django.core.management.base import BaseCommand
from authentication.models import User
from department.models import Department
from teacher.models import Teacher
from django.db import transaction
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Import teachers from a CSV file using multithreading.'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For thread-safe logging
        self.log_queue = Queue()
        self.success_count = 0
        self.error_count = 0
        self.skip_count = 0
        self.lock = threading.Lock()
        
    def log_message(self, level, message):
        """Add log message to queue for thread-safe logging"""
        self.log_queue.put((level, message))
    
    def process_log_queue(self):
        """Process log messages from the queue"""
        while not self.log_queue.empty():
            level, message = self.log_queue.get()
            if level == 'SUCCESS':
                self.stdout.write(self.style.SUCCESS(message))
            elif level == 'ERROR':
                self.stdout.write(self.style.ERROR(message))
            elif level == 'WARNING':
                self.stdout.write(self.style.WARNING(message))
            else:
                self.stdout.write(message)
            self.log_queue.task_done()
    
    def process_teacher_row(self, row):
        """Process a single teacher row"""
        email = row.get('email', '').strip()
        if not email:
            self.log_message('WARNING', "Missing email in row. Skipping.")
            with self.lock:
                self.skip_count += 1
            return
        
        try:
            # Get the user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                self.log_message('WARNING', f"User with email {email} not found. Skipping.")
                with self.lock:
                    self.skip_count += 1
                return
            
            # Get the department
            dept_name = row.get('department_name', '').strip()
            if not dept_name:
                self.log_message('WARNING', f"Missing department name for {email}. Skipping.")
                with self.lock:
                    self.skip_count += 1
                return
            
            try:
                department = Department.objects.get(dept_name=dept_name)
            except Department.DoesNotExist:
                self.log_message('WARNING', f"Department '{dept_name}' not found for {email}. Skipping.")
                with self.lock:
                    self.skip_count += 1
                return
            
            # Check if teacher already exists
            if Teacher.objects.filter(teacher_id=user).exists():
                self.log_message('WARNING', f"Teacher with email {email} already exists. Skipping.")
                with self.lock:
                    self.skip_count += 1
                return
            
            # Create the teacher
            try:
                with transaction.atomic():
                    Teacher.objects.create(
                        teacher_id=user,
                        dept_id=department,
                        staff_code=row.get('staff_code', '').strip(),
                        teacher_specialisation=row.get('specialization', '').strip(),
                        teacher_working_hours=int(row.get('teacher_working_hours') or 0),
                        teacher_role=row.get('teacher_role', '').strip(),
                        availability_type=row.get('availability_type', '').strip(),
                        is_industry_professional=row.get('is_industry_professional', '').strip().lower() == 'true'
                    )
                self.log_message('SUCCESS', f"Teacher {user.first_name} {user.last_name} added successfully.")
                with self.lock:
                    self.success_count += 1
            except Exception as e:
                self.log_message('ERROR', f"Error adding teacher for {email}: {e}")
                with self.lock:
                    self.error_count += 1
                
        except Exception as e:
            self.log_message('ERROR', f"Unexpected error processing row for {email}: {e}")
            with self.lock:
                self.error_count += 1
    
    def handle(self, *args, **options):
        csv_path = os.path.join(settings.BASE_DIR, 'csv', 'updated_data', 'updated_teachers.csv') 
        
        try:
            # Read all rows from CSV
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
            self.stdout.write(f"Starting import of {len(rows)} teachers with threading...")
            
            # Use ThreadPoolExecutor to process rows in parallel
            # Adjust max_workers based on your system capabilities and database connection pool
            max_workers = min(32, len(rows))  # Limit threads to 32 or number of rows
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all rows to the executor
                futures = [executor.submit(self.process_teacher_row, row) for row in rows]
                
                # Process log messages while waiting for threads to complete
                import time
                while any(not future.done() for future in futures):
                    self.process_log_queue()
                    time.sleep(0.1)  # Short sleep to prevent CPU hogging
            
            # Process any remaining log messages
            self.process_log_queue()
            
            # Print summary
            self.stdout.write(self.style.SUCCESS(f"Import completed. Summary:"))
            self.stdout.write(f"- Successfully imported: {self.success_count}")
            self.stdout.write(f"- Skipped: {self.skip_count}")
            self.stdout.write(f"- Errors: {self.error_count}")
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"CSV file not found at: {csv_path}"))