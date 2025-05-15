import django
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UniversityApp.settings')
django.setup()

from rooms.models import Room

rooms = Room.objects.filter()

for i in rooms:
    if 'A' in i.room_number:
        i.block = 'A Block'
        i.save()
    elif 'B' in i.room_number:
        i.block = 'B Block'
        i.save()
    elif 'C' in i.room_number:
        i.block = 'C Block'
        i.save()
    elif 'D' in i.room_number:
        i.block = 'D Block'
        i.save()
    elif 'K' in i.room_number:`
        i.block = "K Block"
        i.save()
    elif 'TIFAC' in i.room_number:
        i.block = "Architecture Block"
        i.save()
    elif 'J' in i.room_number:
        i.block = "J Block"
        i.save()
    elif 'TL' in i.room_number:
        i.block = "Techlounge"
        i.save()
    elif 'WS' in i.room_number:
        i.block = "Workshop Shed"
        i.save()`