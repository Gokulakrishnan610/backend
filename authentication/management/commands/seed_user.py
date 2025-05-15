import csv
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from django.core.management.base import BaseCommand
from authentication.models import User
from django.db import IntegrityError, transaction

class Command(BaseCommand):
    help = 'Import users from CSV into the database using threading for faster processing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--threads',
            type=int,
            default=10,
            help='Number of worker threads to use (default: 10)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of users to process in each batch (default: 100)'
        )
        parser.add_argument(
            '--file',
            type=str,
            default='data/app_users.csv',
            help='Path to the CSV file (default: data/app_users.csv)'
        )

    def handle(self, *args, **options):
        thread_count = options['threads']
        batch_size = options['batch_size']
        file_path = options['file']
        
        self.stdout.write(f"Starting import with {thread_count} threads")
        self.import_users(file_path, thread_count, batch_size)
        self.stdout.write(self.style.SUCCESS("Import completed successfully"))

    def import_users(self, file_path, thread_count, batch_size):
        # Get the allowed user_type values from the User model choices
        self.valid_user_types = {choice[0] for choice in User.USER_TYPE}
        
        # Create a queue to store results for reporting
        self.result_queue = queue.Queue()
        
        # Create a thread to process and display results
        result_thread = threading.Thread(target=self._process_results)
        result_thread.daemon = True
        result_thread.start()
        
        # Read the CSV file and process rows in batches
        with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            
        # Create batches
        batches = [rows[i:i + batch_size] for i in range(0, len(rows), batch_size)]
        self.stdout.write(f"Processing {len(rows)} users in {len(batches)} batches")
        
        # Process batches using thread pool
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            executor.map(self._process_batch, batches)
            
        # Signal the result processor that we're done
        self.result_queue.put(None)
        result_thread.join()
        
    def _process_batch(self, batch):
        """Process a batch of rows from the CSV"""
        for row in batch:
            try:
                with transaction.atomic():  # Use transaction for atomicity
                    self._process_user(row)
            except Exception as e:
                # Log error but continue processing
                self.result_queue.put((f"Error processing {row.get('email', 'unknown')}: {str(e)}", False))
                
    def _process_user(self, row):
        """Process a single user from the CSV"""
        # Trim and split the full name
        name = row['name'].strip()
        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Normalize and validate user_type
        raw_type = row['user_type'].strip().lower()
        user_type = raw_type if raw_type in self.valid_user_types else 'student'
        
        # Determine role flags
        is_staff = user_type == 'teacher'
        is_superuser = False
        
        # Trim email and password fields
        email = row['email'].strip()
        password = row['password'].strip()
        
        # Create or get user
        try:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'password': password,
                    'is_active': True,
                    'is_staff': is_staff,
                    'is_superuser': is_superuser,
                    'phone_number': '',
                    'gender': 'M',
                    'user_type': user_type
                }
            )
            status = 'created' if created else 'exists'
            self.result_queue.put((f"User {status}: {user.email}", True))
        except IntegrityError:
            self.result_queue.put((f"Integrity error for user: {email}", False))
    
    def _process_results(self):
        """Process results from the queue and display them"""
        success_count = 0
        error_count = 0
        
        while True:
            result = self.result_queue.get()
            if result is None:  # Signal to exit
                break
                
            message, success = result
            if success:
                success_count += 1
                if success_count % 100 == 0:  # Only print every 100th success
                    self.stdout.write(f"Progress: {success_count} users processed successfully")
            else:
                error_count += 1
                self.stdout.write(self.style.WARNING(message))
            
            self.result_queue.task_done()
        
        # Print final summary
        self.stdout.write(f"Import complete. {success_count} users processed successfully, {error_count} errors")