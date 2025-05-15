from django.core.management.base import BaseCommand
from django.db import transaction
from slot.models import Slot  # Your Slot model is in the 'slot' app

class Command(BaseCommand):
    help = 'Seed custom time slots into the database'

    def handle(self, *args, **kwargs):
        self.seed_slots()

    def seed_slots(self):
        """Create custom time slots for classes."""
        self.stdout.write(self.style.SUCCESS('📌 Creating custom time slots...'))

        # Check if slots already exist
        if Slot.objects.exists():
            self.stdout.write(self.style.WARNING('⚠️ Slots already exist. Skipping.'))
            return

        # Define custom slots
        slots = [
            ('A', '08:00:00', '15:00:00'),
            ('B', '10:00:00', '17:00:00'),
            ('C', '12:00:00', '19:00:00'),
        ]

        created_count = 0
        with transaction.atomic():
            for slot_name, start_time, end_time in slots:
                Slot.objects.create(
                    slot_name=slot_name,
                    slot_start_time=start_time,
                    slot_end_time=end_time
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {created_count} custom time slots.'))
