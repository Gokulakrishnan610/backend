import os
import csv
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from course.models import Course
from teacher.models import Teacher
from teacherCourse.models import TeacherCourse
from slot.models import Slot
from rooms.models import Room
from .models import Timetable, TimetableGenerationConfig

# Import OR-Tools for constraint programming
try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    logging.warning("OR-Tools not available. Timetable generation will be limited.")

logger = logging.getLogger(__name__)

class TimetableGenerationService:
    """Service for generating timetables using OR-Tools constraint programming"""
    
    def __init__(self, config_id=None):
        """Initialize the timetable generation service"""
        self.config = None
        if config_id:
            try:
                self.config = TimetableGenerationConfig.objects.get(id=config_id)
            except TimetableGenerationConfig.DoesNotExist:
                logger.error(f"Timetable generation config {config_id} not found")
        
        # Constants
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        self.day_indices = {day: i for i, day in enumerate(self.days)}
        
        # Data structures
        self.teachers = []
        self.courses = []
        self.rooms = []
        self.slots = []
        
        # Mapping dictionaries
        self.teacher_courses = {}  # Teacher -> courses
        self.course_teachers = {}  # Course -> teachers
        self.room_capacities = {}  # Room -> capacity
        self.lab_rooms = set()     # Set of lab rooms
        
        # Course types
        self.lab_courses = set()    # Set of lab courses
        self.theory_courses = set() # Set of theory courses
        
        # Load data from database
        self._load_data_from_db()
        
    def _load_data_from_db(self):
        """Load data from the database"""
        logger.info("Loading data from database...")
        
        # Load teachers
        self.teachers = list(Teacher.objects.all().values_list('id', flat=True))
        
        # Load courses
        self.courses = list(Course.objects.all().values_list('id', flat=True))
        
        # Identify lab courses
        lab_courses = Course.objects.filter(practical_hours__gt=0)
        self.lab_courses = set(lab_courses.values_list('id', flat=True))
        
        # Identify theory courses
        self.theory_courses = set(self.courses) - self.lab_courses
        
        # Load rooms
        self.rooms = list(Room.objects.all().values_list('id', flat=True))
        
        # Identify lab rooms
        lab_rooms = Room.objects.filter(is_lab=True)
        self.lab_rooms = set(lab_rooms.values_list('id', flat=True))
        
        # Load room capacities
        for room in Room.objects.all():
            self.room_capacities[room.id] = room.room_max_cap
        
        # Load slots
        self.slots = list(Slot.objects.all().values_list('id', flat=True))
        
        # Load teacher-course assignments
        for tc in TeacherCourse.objects.all():
            teacher_id = tc.teacher_id_id
            course_id = tc.course_id_id
            
            if teacher_id not in self.teacher_courses:
                self.teacher_courses[teacher_id] = []
            self.teacher_courses[teacher_id].append(course_id)
            
            if course_id not in self.course_teachers:
                self.course_teachers[course_id] = []
            self.course_teachers[course_id].append(teacher_id)
        
        logger.info(f"Loaded: {len(self.teachers)} teachers, {len(self.courses)} courses, "
                   f"{len(self.rooms)} rooms, {len(self.slots)} slots")
    
    def generate_timetable(self, config=None):
        """Generate timetable using OR-Tools CP-SAT Solver"""
        if not ORTOOLS_AVAILABLE:
            logger.error("OR-Tools not available. Cannot generate timetable.")
            return False
        
        if config:
            self.config = config
        
        if not self.config:
            logger.error("No configuration provided for timetable generation")
            return False
        
        # Update generation status
        self.config.is_generated = False
        self.config.generation_started_at = timezone.now()
        self.config.generation_log = "Started timetable generation\n"
        self.config.save()
        
        try:
            # Create the model
            model = cp_model.CpModel()
            
            # Create variables
            # x[t][c][r][d][s] = 1 if teacher t teaches course c in room r on day d during slot s
            x = {}
            
            for t_idx, teacher_id in enumerate(self.teachers):
                # Skip teachers without assigned courses
                teacher_courses = self.teacher_courses.get(teacher_id, [])
                if not teacher_courses:
                    continue
                
                for c_idx, course_id in enumerate(teacher_courses):
                    for r_idx, room_id in enumerate(self.rooms):
                        # Check room type compatibility
                        is_lab_course = course_id in self.lab_courses
                        is_lab_room = room_id in self.lab_rooms
                        
                        # Skip incompatible room assignments
                        if (is_lab_course and not is_lab_room) or (not is_lab_course and is_lab_room):
                            continue
                        
                        for d_idx, day in enumerate(self.days):
                            for s_idx, slot_id in enumerate(self.slots):
                                x[t_idx, c_idx, r_idx, d_idx, s_idx] = model.NewBoolVar(
                                    f'x[{t_idx}][{c_idx}][{r_idx}][{d_idx}][{s_idx}]')
            
            # Add constraints
            log_message = "Adding constraints...\n"
            
            # Constraint: Each course must be taught at least N times per week
            min_course_instances = self.config.min_course_instances
            for t_idx, teacher_id in enumerate(self.teachers):
                for c_idx, course_id in enumerate(self.teacher_courses.get(teacher_id, [])):
                    # Sum all slots for this teacher-course combination
                    course_slots = []
                    for r_idx, _ in enumerate(self.rooms):
                        for d_idx, _ in enumerate(self.days):
                            for s_idx, _ in enumerate(self.slots):
                                if (t_idx, c_idx, r_idx, d_idx, s_idx) in x:
                                    course_slots.append(x[t_idx, c_idx, r_idx, d_idx, s_idx])
                    
                    # Each course must be taught at least min_course_instances times
                    if course_slots:
                        model.Add(sum(course_slots) >= min_course_instances)
            
            log_message += f"- Each course must be taught at least {min_course_instances} times per week\n"
            
            # Constraint: No teacher can teach two courses in the same slot
            for t_idx, teacher_id in enumerate(self.teachers):
                for d_idx, _ in enumerate(self.days):
                    for s_idx, _ in enumerate(self.slots):
                        # Find all courses this teacher could teach in this slot
                        slot_assignments = []
                        for c_idx, course_id in enumerate(self.teacher_courses.get(teacher_id, [])):
                            for r_idx, _ in enumerate(self.rooms):
                                if (t_idx, c_idx, r_idx, d_idx, s_idx) in x:
                                    slot_assignments.append(x[t_idx, c_idx, r_idx, d_idx, s_idx])
                        
                        # Teacher can teach at most one course in this slot
                        if slot_assignments:
                            model.Add(sum(slot_assignments) <= 1)
            
            log_message += "- No teacher can teach two courses in the same slot\n"
            
            # Constraint: Each room can have at most one course in a given slot
            for r_idx, room_id in enumerate(self.rooms):
                for d_idx, _ in enumerate(self.days):
                    for s_idx, _ in enumerate(self.slots):
                        # Find all possible courses in this room at this slot
                        room_assignments = []
                        for t_idx, teacher_id in enumerate(self.teachers):
                            for c_idx, course_id in enumerate(self.teacher_courses.get(teacher_id, [])):
                                if (t_idx, c_idx, r_idx, d_idx, s_idx) in x:
                                    room_assignments.append(x[t_idx, c_idx, r_idx, d_idx, s_idx])
                        
                        # Room can have at most one course in this slot
                        if room_assignments:
                            model.Add(sum(room_assignments) <= 1)
            
            log_message += "- Each room can have at most one course in a given slot\n"
            
            # Constraint: Maximum teaching hours per day for each teacher
            if self.config.max_teacher_slots_per_day > 0:
                for t_idx, teacher_id in enumerate(self.teachers):
                    for d_idx, _ in enumerate(self.days):
                        # Find all slots this teacher teaches on this day
                        day_slots = []
                        for c_idx, course_id in enumerate(self.teacher_courses.get(teacher_id, [])):
                            for r_idx, _ in enumerate(self.rooms):
                                for s_idx, _ in enumerate(self.slots):
                                    if (t_idx, c_idx, r_idx, d_idx, s_idx) in x:
                                        day_slots.append(x[t_idx, c_idx, r_idx, d_idx, s_idx])
                        
                        # Teacher can teach at most max_teacher_slots_per_day on this day
                        if day_slots:
                            model.Add(sum(day_slots) <= self.config.max_teacher_slots_per_day)
                
                log_message += f"- Maximum {self.config.max_teacher_slots_per_day} teaching hours per day for each teacher\n"
            
            # Update log
            self.config.generation_log += log_message
            self.config.save()
            
            # Create the solver and solve
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = self.config.solver_timeout
            
            status = solver.Solve(model)
            
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                # Solution found
                log_message = f"Solution found with status: {solver.StatusName(status)}\n"
                log_message += f"Wall time: {solver.WallTime()} seconds\n"
                
                # Create timetable entries
                with transaction.atomic():
                    # Clear existing timetable
                    Timetable.objects.all().delete()
                    
                    # Create new timetable entries
                    for t_idx, teacher_id in enumerate(self.teachers):
                        for c_idx, course_id in enumerate(self.teacher_courses.get(teacher_id, [])):
                            for r_idx, room_id in enumerate(self.rooms):
                                for d_idx, day in enumerate(self.days):
                                    for s_idx, slot_id in enumerate(self.slots):
                                        if (t_idx, c_idx, r_idx, d_idx, s_idx) in x:
                                            if solver.Value(x[t_idx, c_idx, r_idx, d_idx, s_idx]) == 1:
                                                # Get teacher-course assignment
                                                teacher_course = TeacherCourse.objects.get(
                                                    teacher_id=teacher_id,
                                                    course_id=course_id
                                                )
                                                
                                                # Get slot and room objects
                                                slot = Slot.objects.get(id=slot_id)
                                                room = Room.objects.get(id=room_id)
                                                
                                                # Create timetable entry
                                                Timetable.objects.create(
                                                    day_of_week=d_idx,
                                                    course_assignment=teacher_course,
                                                    slot=slot,
                                                    room=room,
                                                    is_recurring=True,
                                                    start_date=timezone.now().date(),
                                                    session_type='Lecture' if course_id in self.theory_courses else 'Lab'
                                                )
                
                # Update status
                self.config.is_generated = True
                self.config.generation_completed_at = timezone.now()
                self.config.generation_log += log_message
                self.config.save()
                
                return True
            else:
                # No solution found
                log_message = f"No solution found. Status: {solver.StatusName(status)}\n"
                log_message += f"Wall time: {solver.WallTime()} seconds\n"
                
                self.config.is_generated = False
                self.config.generation_completed_at = timezone.now()
                self.config.generation_log += log_message
                self.config.save()
                
                return False
                
        except Exception as e:
            logger.exception("Error generating timetable")
            self.config.is_generated = False
            self.config.generation_completed_at = timezone.now()
            self.config.generation_log += f"Error: {str(e)}\n"
            self.config.save()
            
            return False 