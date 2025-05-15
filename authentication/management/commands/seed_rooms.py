import csv
from django.core.management.base import BaseCommand
from rooms.models import Room
from department.models import Department
from django.db import transaction
import os
from django.conf import settings

# Mapping from CSV to Room model fields
type_map = {
    'Room': 'Classroom',
    'NTL': 'Laboratory',
}

tech_map = {
    'Low': 'Basic',
    'Medium': 'Advanced',
    'High': 'High-tech',
    '': 'None',
    None: 'None'
}

class Command(BaseCommand):
    help = 'Import rooms from a hardcoded CSV file path'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'csv', 'updated_rooms.csv') 
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    dept_name = row['maintained_by_id'].strip()
                    try:
                        # ✅ Fixed: use dept_name instead of name
                        department = Department.objects.get(dept_name=dept_name)
                    except Department.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"⚠️ Department not found: {dept_name}"))
                        continue

                    room_type = type_map.get(row['room_type'].strip(), 'Classroom')
                    tech_level = tech_map.get(row['tech_level'].strip(), 'None')

                    room = Room(
                        room_number=row['room_number'].strip(),
                        block=row['block'].strip(),
                        description=row['description'].strip(),
                        is_lab=row['is_lab'].strip().lower() == 'true',
                        room_type=room_type,
                        room_min_cap=int(float(row['room_min_cap'])),
                        room_max_cap=int(float(row['room_max_cap'])),
                        has_projector=row['has_projector'].strip().lower() == 'true',
                        has_ac=row['has_ac'].strip().lower() == 'true',
                        tech_level=tech_level,
                        maintained_by_id=department
                    )
                    room.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Imported: {room.room_number}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"❌ File not found: {file_path}"))
