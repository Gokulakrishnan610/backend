import csv
import os
from django.core.management.base import BaseCommand
from department.models import Department
from django.conf import settings

class Command(BaseCommand):
    help = 'Seed departments from CSV file'

    def handle(self, *args, **kwargs):
        # Construct the absolute path to the CSV file
        csv_file_path = os.path.join(settings.BASE_DIR, 'csv', 'updated_data', 'departments.csv')
        
        with open(csv_file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Create or update the department
                department, created = Department.objects.get_or_create(
                    dept_name=row['dept_name'],
                    defaults={
                        'date_established': row['date_established'],
                        'contact_info': row['contact_info'],
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created department: {department.dept_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Department already exists: {department.dept_name}'))
