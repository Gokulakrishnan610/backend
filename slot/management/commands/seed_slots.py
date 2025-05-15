from django.core.management.base import BaseCommand
from slot.models import Slot
from datetime import datetime, timedelta
import logging
import traceback

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Seeds the database with detailed time slots (50-min slots with 10-min gaps) within the predefined slot types A, B, C'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of all slots without confirmation',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Enable verbose output
        self.stdout.write(self.style.WARNING('Starting detailed slot seeding process...'))
        
        try:
            # Check for existing slots
            existing_slots = Slot.objects.all()
            default_slots = {'A', 'B', 'C'}
            
            # Count custom slots (non A, B, or C)
            custom_slots = [s for s in existing_slots if s.slot_name not in default_slots]
            self.stdout.write(self.style.WARNING(f'Found {len(existing_slots)} slots ({len(custom_slots)} custom).'))
            
            if custom_slots and not force:
                # Ask for confirmation
                confirm = input('Custom slots already exist. Delete and recreate them? (y/n): ')
                if confirm.lower() != 'y':
                    self.stdout.write(self.style.WARNING('Aborted. No slots were created.'))
                    return
            
            # Delete custom slots if they exist
            if custom_slots:
                self.stdout.write(self.style.WARNING(f'Deleting {len(custom_slots)} custom slots...'))
                for slot in custom_slots:
                    slot.delete()
                self.stdout.write(self.style.SUCCESS('Deleted custom slots.'))
            
            # Make sure we have the three default slots (A, B, C)
            self._ensure_default_slots()
                
            # Create detailed time slots within each default slot type
            self._create_slots_for_type('A', '08:00', '15:00', force) 
            self._create_slots_for_type('B', '10:00', '17:00', force)
            self._create_slots_for_type('C', '12:00', '19:00', force)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
    
    def _ensure_default_slots(self):
        """Ensure the three default slots (A, B, C) exist"""
        for slot_type, times in [
            ('A', ('08:00:00', '15:00:00')),
            ('B', ('10:00:00', '17:00:00')),
            ('C', ('12:00:00', '19:00:00'))
        ]:
            if not Slot.objects.filter(slot_type=slot_type, slot_name=f'Slot {slot_type}').exists():
                self.stdout.write(f'Creating default slot {slot_type}')
                slot = Slot(
                    slot_name=f'Slot {slot_type}',
                    slot_type=slot_type,
                    slot_start_time=times[0],
                    slot_end_time=times[1]
                )
                slot.save()
    
    def _create_slots_for_type(self, slot_type, start_time_str, end_time_str, force):
        """Create detailed slots within a given slot type (A, B, or C)"""
        self.stdout.write(self.style.WARNING(f'Creating detailed slots for Slot Type {slot_type}...'))
        
        # Parse times
        start_time = datetime.strptime(start_time_str, '%H:%M')
        end_time = datetime.strptime(end_time_str, '%H:%M')
        
        self.stdout.write(f'Time range: {start_time.strftime("%H:%M")} - {end_time.strftime("%H:%M")}')
        
        # Get existing detailed slots for this type
        existing_slots = Slot.objects.filter(slot_type=slot_type).exclude(slot_name=f'Slot {slot_type}')
        if existing_slots and not force:
            self.stdout.write(self.style.WARNING(
                f'Skipping Slot Type {slot_type}: {len(existing_slots)} detailed slots already exist'
            ))
            return
        
        if existing_slots:
            self.stdout.write(f'Deleting {len(existing_slots)} existing detailed slots for type {slot_type}')
            existing_slots.delete()
        
        # Generate slots (50 min with 10 min breaks)
        slot_number = 1
        current_time = start_time
        created_count = 0
        
        while current_time < end_time:
            # Calculate end of slot (50 minutes after start)
            slot_end_time = current_time + timedelta(minutes=50)
            
            if slot_end_time > end_time:
                break
            
            slot_name = f"{slot_type}{slot_number}"
            formatted_start = current_time.strftime('%H:%M')
            formatted_end = slot_end_time.strftime('%H:%M')
            
            self.stdout.write(f'Creating slot: {slot_name}, time={formatted_start}-{formatted_end}')
            
            try:
                new_slot = Slot(
                    slot_name=slot_name,
                    slot_type=slot_type,
                    slot_start_time=formatted_start,
                    slot_end_time=formatted_end
                )
                new_slot.save()
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created {slot_name}: {formatted_start} - {formatted_end}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating {slot_name}: {str(e)}")
                )
                self.stdout.write(self.style.ERROR(traceback.format_exc()))
            
            # Move to next slot (50 minutes + 10 minute gap = 60 minutes)
            current_time += timedelta(minutes=60)
            slot_number += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} detailed slots for type {slot_type}')) 