from django.db import models

# Create your models here.
class Room(models.Model):
    ROOM_TYPES = [
        ('Class-Room', 'Class Room'),
        ('Computer-Lab', 'Computer Lab'),
        ('Core-Lab', 'Core Lab'),
    ]
    TECH_LEVEL = [
        ('None', 'None'),
        ('Basic', 'Basic'),
        ('Advanced', 'Advanced'),
        ('High-tech', 'High-tech')
    ]

    room_number = models.CharField("Room Number", max_length=20)
    block = models.CharField("Block", max_length=100)
    description = models.TextField("Description", blank=True)
    maintained_by_id = models.ForeignKey("department.Department", on_delete=models.SET_NULL, null=True, related_name="maintained_rooms")
    is_lab = models.BooleanField("Is Lab", default=False)
    room_type = models.CharField("Room Type", max_length=50, choices=ROOM_TYPES)
    room_min_cap = models.IntegerField("Minimum Capacity", default=0)
    room_max_cap = models.IntegerField("Maximum Capacity", default=0)
    tech_level = models.CharField("Technology Level", max_length=50, choices=TECH_LEVEL, default='None')
    has_projector = models.BooleanField("Has Projector", default=False)
    has_ac = models.BooleanField("Has AC", default=False)
    smart_board = models.BooleanField("Smart Board", default=False)
    green_board = models.BooleanField("Green Board", default=False)
    isLcsAvailable = models.BooleanField("Is LCS Available", default=False)

    def __str__(self):
        return f"{self.room_number} ({self.block})"