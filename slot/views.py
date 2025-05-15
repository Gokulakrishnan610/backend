from django.shortcuts import render
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.views import APIView
from authentication.authentication import JWTCookieAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import SlotSerializer, TeacherSlotAssignmentSerializer
from .models import Slot, TeacherSlotAssignment
from teacher.models import Teacher
from department.models import Department
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from collections import Counter

# Create your views here.
class SlotListView(ListAPIView):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SlotSerializer

    def get_queryset(self):
        slots = Slot.objects.all().order_by('slot_type', 'slot_start_time')
        return slots

class TeacherSlotPreferenceView(CreateAPIView):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SlotSerializer

    def post(self, request, *args, **kwargs):
        try:
            teacher = Teacher.objects.get(id=request.data.get('teacher_id'))
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher not found."}, status=status.HTTP_404_NOT_FOUND)
        
        operations = request.data.get('operations', [])
        
        if not operations:
            return Response({"error": "No operations provided."}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        success_count = 0
        
        with transaction.atomic():
            for operation in operations:
                action = operation.get('action', 'create').lower()
                result = {
                    "action": action,
                    "slot_id": operation.get('slot_id'),
                    "day_of_week": operation.get('day_of_week'),
                    "success": False
                }
                
                try:
                    if action in ['create', 'update']:
                        response = self._handle_create_update(teacher, operation)
                    elif action == 'delete':
                        response = self._handle_delete(teacher, operation)
                    else:
                        raise DRFValidationError(f"Invalid action: {action}")
                    
                    result.update(response)
                    result["success"] = True
                    success_count += 1
                except (ValidationError, DRFValidationError) as e:
                    result["error"] = e.message_dict if hasattr(e, 'message_dict') else str(e)
                except Exception as e:
                    result["error"] = str(e)
                
                results.append(result)
        
        if success_count == 0:
            status_code = status.HTTP_400_BAD_REQUEST
        elif success_count == len(operations):
            status_code = status.HTTP_201_CREATED
        else:
            status_code = status.HTTP_207_MULTI_STATUS
        
        return Response(
            {
                "results": results,
                "success_count": success_count,
                "total_operations": len(operations)
            },
            status=status_code
        )

    def _handle_create_update(self, teacher, data):
        if 'slot_id' not in data or 'day_of_week' not in data:
            raise DRFValidationError("Both 'slot_id' and 'day_of_week' are required.")
        
        slot_id = data['slot_id']
        day_of_week = data['day_of_week']
        
        try:
            slot = Slot.objects.get(pk=slot_id)
        except Slot.DoesNotExist:
            raise DRFValidationError(f"Slot with id {slot_id} does not exist.")
        
        # Check 5-day week constraint
        current_days = TeacherSlotAssignment.objects.filter(
            teacher=teacher
        ).values_list('day_of_week', flat=True).distinct()
        
        if len(current_days) >= 5 and day_of_week not in current_days:
            raise DRFValidationError("Teacher already has assignments for 5 days. Maximum is 5 days per week.")
        
        # Check Monday/Saturday constraint - only one of these days allowed
        if day_of_week in TeacherSlotAssignment.RESTRICTED_DAYS:
            restricted_day_assignments = TeacherSlotAssignment.objects.filter(
                teacher=teacher,
                day_of_week__in=TeacherSlotAssignment.RESTRICTED_DAYS
            ).exclude(day_of_week=day_of_week)
            
            if restricted_day_assignments.exists():
                restricted_day = dict(TeacherSlotAssignment.DAYS_OF_WEEK)[restricted_day_assignments.first().day_of_week]
                raise DRFValidationError(
                    f"Teacher already has a slot assigned for {restricted_day}. "
                    f"Teachers can only choose one of these days: Monday or Saturday."
                )
        
        # Check slot type distribution constraint
        self._validate_slot_type_distribution(teacher, slot, day_of_week)
        
        # Check department distribution constraint (33% per slot type)
        if teacher.dept_id:
            dept_id = teacher.dept_id.id
            total_dept_teachers = Teacher.objects.filter(dept_id=dept_id).count()
            
            if total_dept_teachers > 0:
                # Get count of teachers in this department assigned to this slot type on this day
                teachers_in_slot = TeacherSlotAssignment.objects.filter(
                    teacher__dept_id=dept_id,
                    day_of_week=day_of_week,
                    slot__slot_type=slot.slot_type
                ).values('teacher').distinct().count()
                
                # Calculate max teachers allowed (33% of department + 1 extra teacher)
                max_teachers_per_slot = int((total_dept_teachers * 0.33) + 0.5) + 1  # Adding 1 to allow one extra teacher
                
                if teachers_in_slot >= max_teachers_per_slot:
                    raise DRFValidationError(
                        f"Maximum number of teachers (33% + 1) from department {teacher.dept_id.dept_name} "
                        f"already assigned to slot type {slot.slot_type} on {dict(TeacherSlotAssignment.DAYS_OF_WEEK)[day_of_week]}."
                    )
        
        assignment, created = TeacherSlotAssignment.objects.get_or_create(
            teacher=teacher,
            day_of_week=day_of_week,
            defaults={'slot': slot}
        )
        
        if not created:
            assignment.slot = slot
            assignment.full_clean()
            assignment.save()
            action = "updated"
        else:
            action = "created"
        
        return {
            "message": f"Slot assignment {action} successfully.",
            "created": created
        }

    def _validate_slot_type_distribution(self, teacher, new_slot, new_day_of_week):
        """
        Validate that the teacher's slot choices follow the required distribution format:
        Valid combinations: A-2/B-2/C-1, A-1/B-2/C-2, or A-2/B-1/C-2
        """
        # Get all current assignments for this teacher
        current_assignments = list(TeacherSlotAssignment.objects.filter(
            teacher=teacher
        ).exclude(day_of_week=new_day_of_week).values_list('slot__slot_type', flat=True))
        
        # Add the new slot type to the distribution
        current_assignments.append(new_slot.slot_type)
        
        # Count occurrences of each slot type
        slot_type_counts = Counter(current_assignments)
        total_assignments = len(current_assignments)
        
        # Don't need to check if less than 5 assignments
        if total_assignments > 5:
            raise DRFValidationError("Teacher cannot have more than 5 slot assignments in total.")
        
        # When we reach 5 assignments, ensure we have a valid combination
        if total_assignments == 5:
            # Valid combinations
            valid_combinations = [
                # Format: {A: count, B: count, C: count}
                {'A': 2, 'B': 2, 'C': 1},
                {'A': 1, 'B': 2, 'C': 2},
                {'A': 2, 'B': 1, 'C': 2}
            ]
            
            is_valid = False
            for combo in valid_combinations:
                if all(slot_type_counts.get(slot_type, 0) == count for slot_type, count in combo.items()):
                    is_valid = True
                    break
            
            if not is_valid:
                slot_a_count = slot_type_counts.get('A', 0)
                slot_b_count = slot_type_counts.get('B', 0)
                slot_c_count = slot_type_counts.get('C', 0)
                
                raise DRFValidationError(
                    f"Invalid slot distribution. Current distribution is: "
                    f"A: {slot_a_count}, B: {slot_b_count}, C: {slot_c_count}. "
                    f"Valid distributions for 5 days are: A-2/B-2/C-1, A-1/B-2/C-2, or A-2/B-1/C-2."
                )

    def _handle_delete(self, teacher, data):
        if 'slot_id' not in data or 'day_of_week' not in data:
            raise DRFValidationError("Both 'slot_id' and 'day_of_week' are required.")
        
        slot_id = data['slot_id']
        day_of_week = data['day_of_week']
        
        try:
            assignment = TeacherSlotAssignment.objects.get(
                teacher=teacher,
                slot_id=slot_id,
                day_of_week=day_of_week
            )
            assignment.delete()
            return {"message": "Slot assignment deleted successfully."}
        except TeacherSlotAssignment.DoesNotExist:
            raise DRFValidationError("Slot assignment not found.")
    
class TeacherSlotListView(ListAPIView):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherSlotAssignmentSerializer
    queryset = TeacherSlotAssignment.objects.all().select_related('slot', 'teacher')

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by teacher if teacher_id is provided
        teacher_id = self.request.query_params.get('teacher_id')
        if teacher_id:
            queryset = queryset.filter(teacher__id=teacher_id)
        
        # Filter by department if dept_id is provided
        dept_id = self.request.query_params.get('dept_id')
        if dept_id:
            queryset = queryset.filter(teacher__dept_id=dept_id)
        
        # Filter by day if day_of_week is provided
        day_of_week = self.request.query_params.get('day_of_week')
        if day_of_week:
            queryset = queryset.filter(day_of_week=day_of_week)
        
        # Filter by slot type if slot_type is provided
        slot_type = self.request.query_params.get('slot_type')
        if slot_type:
            queryset = queryset.filter(slot__slot_type=slot_type)
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate summary statistics
        include_stats = request.query_params.get('include_stats', 'false').lower() == 'true'
        
        if include_stats:
            stats = self._calculate_stats(queryset)
            return Response({
                'assignments': serializer.data,
                'stats': stats
            })
        
        return Response(serializer.data)
    
    def _calculate_stats(self, queryset):
        # Get unique teachers and departments in the queryset
        teacher_ids = queryset.values_list('teacher', flat=True).distinct()
        dept_ids = Teacher.objects.filter(id__in=teacher_ids).values_list('dept_id', flat=True).distinct()
        
        stats = {
            'total_assignments': queryset.count(),
            'teacher_count': len(teacher_ids),
            'department_distribution': [],
            'slot_type_distribution': {},
            'day_distribution': {}
        }
        
        # Department distribution
        for dept_id in dept_ids:
            if dept_id:
                dept = Department.objects.get(id=dept_id)
                dept_teachers = Teacher.objects.filter(dept_id=dept_id)
                dept_teacher_count = dept_teachers.count()
                
                dept_stats = {
                    'department': dept.dept_name,
                    'total_teachers': dept_teacher_count,
                    'assigned_teachers': Teacher.objects.filter(
                        id__in=teacher_ids, 
                        dept_id=dept_id
                    ).count(),
                    'slot_distribution': {}
                }
                
                # Slot type distribution per department
                for slot_type, _ in Slot.SLOT_TYPES:
                    slot_teachers = queryset.filter(
                        teacher__dept_id=dept_id, 
                        slot__slot_type=slot_type
                    ).values('teacher').distinct().count()
                    
                    dept_stats['slot_distribution'][slot_type] = {
                        'teacher_count': slot_teachers,
                        'percentage': round(slot_teachers / dept_teacher_count * 100, 1) if dept_teacher_count > 0 else 0
                    }
                
                stats['department_distribution'].append(dept_stats)
        
        # Overall slot type distribution
        for slot_type, _ in Slot.SLOT_TYPES:
            stats['slot_type_distribution'][slot_type] = queryset.filter(
                slot__slot_type=slot_type
            ).count()
        
        # Day distribution
        for day_value, day_name in TeacherSlotAssignment.DAYS_OF_WEEK:
            stats['day_distribution'][day_name] = queryset.filter(
                day_of_week=day_value
            ).count()
        
        return stats

class DepartmentSlotSummaryView(APIView):
    """View to provide summary information about department slot allocations"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        dept_id = request.query_params.get('dept_id')
        
        if not dept_id:
            return Response({"error": "Department ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            department = Department.objects.get(id=dept_id)
        except Department.DoesNotExist:
            return Response({"error": "Department not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get all teachers in this department
        teachers = Teacher.objects.filter(dept_id=dept_id)
        total_teachers = teachers.count()
        
        if total_teachers == 0:
            return Response({
                "department": department.dept_name,
                "total_teachers": 0,
                "message": "No teachers in this department"
            })
        
        # Get all assignments for teachers in this department
        assignments = TeacherSlotAssignment.objects.filter(teacher__dept_id=dept_id)
        
        # Count teachers with assignments
        teachers_with_assignments = assignments.values('teacher').distinct().count()
        
        # Prepare data structures for proper counting of unique teachers
        slot_distribution = {}
        day_distribution = {}
        teacher_assignment_count = {}  # Count of days each teacher is assigned
        teachers_per_slot_type = {}    # Unique teachers per slot type
        teachers_per_day = {}          # Unique teachers per day
        
        # Initialize data structures
        for slot_type, slot_name in Slot.SLOT_TYPES:
            slot_distribution[slot_type] = {
                "name": slot_name,
                "days": {}
            }
            teachers_per_slot_type[slot_type] = set()
            
            for day_value, day_name in TeacherSlotAssignment.DAYS_OF_WEEK:
                slot_distribution[slot_type]["days"][day_name] = {
                    "teacher_count": 0,
                    "percentage": 0,
                    "teachers": []
                }
        
        for day_value, day_name in TeacherSlotAssignment.DAYS_OF_WEEK:
            day_distribution[day_name] = {
                "slot_distribution": {},
                "total_teachers": 0
            }
            teachers_per_day[day_name] = set()
            
            for slot_type, slot_name in Slot.SLOT_TYPES:
                day_distribution[day_name]["slot_distribution"][slot_type] = {
                    "teacher_count": 0,
                    "percentage": 0
                }
        
        # Process all assignments
        for assignment in assignments:
            teacher = assignment.teacher
            teacher_id = teacher.id
            slot_type = assignment.slot.slot_type
            day_value = assignment.day_of_week
            day_name = dict(TeacherSlotAssignment.DAYS_OF_WEEK)[day_value]
            
            # Add teacher to slot distribution for this day
            slot_distribution[slot_type]["days"][day_name]["teacher_count"] += 1
            slot_distribution[slot_type]["days"][day_name]["teachers"].append({
                "id": teacher_id,
                "name": str(teacher)
            })
            
            # Track unique teachers per slot type and day
            teachers_per_slot_type[slot_type].add(teacher_id)
            teachers_per_day[day_name].add(teacher_id)
            
            # Update teacher assignment count (days per teacher)
            if teacher_id not in teacher_assignment_count:
                teacher_assignment_count[teacher_id] = {day_name}
            else:
                teacher_assignment_count[teacher_id].add(day_name)
        
        # Calculate percentages for slot distribution
        for slot_type in slot_distribution:
            for day_name in slot_distribution[slot_type]["days"]:
                count = slot_distribution[slot_type]["days"][day_name]["teacher_count"]
                slot_distribution[slot_type]["days"][day_name]["percentage"] = round(count / total_teachers * 100, 1)
        
        # Fill in day distribution with unique teacher counts
        for day_name, teacher_ids in teachers_per_day.items():
            unique_teachers_count = len(teacher_ids)
            day_distribution[day_name]["total_teachers"] = unique_teachers_count
            
            # Count teachers per slot type on this day
            for slot_type in slot_distribution:
                teachers_in_slot_on_day = set()
                for teacher_data in slot_distribution[slot_type]["days"][day_name]["teachers"]:
                    teachers_in_slot_on_day.add(teacher_data["id"])
                
                slot_teacher_count = len(teachers_in_slot_on_day)
                day_distribution[day_name]["slot_distribution"][slot_type]["teacher_count"] = slot_teacher_count
                day_distribution[day_name]["slot_distribution"][slot_type]["percentage"] = round(slot_teacher_count / total_teachers * 100, 1) if total_teachers > 0 else 0
        
        # Count teachers by number of assigned days (based on unique days)
        days_assigned_distribution = {
            "1 day": 0, "2 days": 0, "3 days": 0, "4 days": 0, "5 days": 0
        }
        
        for teacher_id, days in teacher_assignment_count.items():
            day_count = len(days)
            if 1 <= day_count <= 5:
                days_assigned_distribution[f"{day_count} day{'s' if day_count > 1 else ''}"] += 1
        
        # Check compliance with 33% per slot rule
        compliance_status = {"status": "Compliant", "issues": []}
        threshold = int(total_teachers * 0.33 + 0.5) + 1  # Round up and add 1 extra teacher
        
        for slot_type, slot_data in slot_distribution.items():
            for day_name, day_data in slot_data["days"].items():
                if day_data["teacher_count"] > threshold:
                    compliance_status["status"] = "Non-Compliant"
                    compliance_status["issues"].append(
                        f"Slot {slot_type} on {day_name} has {day_data['teacher_count']} teachers "
                        f"({day_data['percentage']}%), exceeding the 33% + 1 threshold of {threshold} teachers."
                    )
        
        # Calculate slot type summary (unique teachers assigned to each slot type)
        slot_type_summary = {}
        for slot_type, teacher_ids in teachers_per_slot_type.items():
            slot_type_summary[slot_type] = {
                "teacher_count": len(teacher_ids),
                "percentage": round(len(teacher_ids) / total_teachers * 100, 1) if total_teachers > 0 else 0
            }
        
        result = {
            "department": department.dept_name,
            "total_teachers": total_teachers,
            "teachers_with_assignments": teachers_with_assignments,
            "unassigned_teachers": total_teachers - teachers_with_assignments,
            "slot_distribution": slot_distribution,
            "day_distribution": day_distribution,
            "days_assigned_distribution": days_assigned_distribution,
            "slot_type_summary": slot_type_summary,
            "compliance": compliance_status
        }
        
        return Response(result)

class InitializeDefaultSlotsView(APIView):
    """View to initialize the three default slot types"""
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        # Create the three default slots if they don't exist
        default_slots = [
            {
                'slot_name': 'Slot A',
                'slot_type': 'A',
                'slot_start_time': '08:00:00',
                'slot_end_time': '15:00:00'
            },
            {
                'slot_name': 'Slot B',
                'slot_type': 'B',
                'slot_start_time': '10:00:00',
                'slot_end_time': '17:00:00'
            },
            {
                'slot_name': 'Slot C',
                'slot_type': 'C',
                'slot_start_time': '12:00:00',
                'slot_end_time': '19:00:00'
            }
        ]
        
        created_slots = []
        existing_slots = []
        
        for slot_data in default_slots:
            # Check if slots with this type already exist
            existing = Slot.objects.filter(slot_type=slot_data['slot_type']).order_by('id')
            
            if existing.exists():
                # If multiple slots exist with this type, use the first one
                slot = existing.first()
                existing_slots.append({
                    'id': slot.id,
                    'slot_name': slot.slot_name,
                    'slot_type': slot.slot_type,
                    'slot_start_time': slot.slot_start_time,
                    'slot_end_time': slot.slot_end_time
                })
            else:
                # Create new slot if none exists
                slot = Slot.objects.create(**slot_data)
                created_slots.append({
                    'id': slot.id,
                    'slot_name': slot.slot_name,
                    'slot_type': slot.slot_type,
                    'slot_start_time': slot.slot_start_time,
                    'slot_end_time': slot.slot_end_time
                })
        
        # Handle duplicate slots - clean up extras if needed
        for slot_type in ['A', 'B', 'C']:
            duplicates = Slot.objects.filter(slot_type=slot_type)[1:]  # Get all but first
            if duplicates.exists():
                # Check if any of these duplicates are referenced by assignments
                for duplicate in duplicates:
                    if not duplicate.teacher_assignments.exists():
                        duplicate.delete()
        
        return Response({
            'created_slots': created_slots,
            'existing_slots': existing_slots,
            'message': f"Created {len(created_slots)} new slots. {len(existing_slots)} slots already existed."
        })

class BatchTeacherSlotAssignmentView(APIView):
    """
    View to handle batch assignment operations for multiple teachers and slots
    This provides better performance and error handling for bulk operations
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        assignments = request.data.get('assignments', [])
        
        if not assignments:
            return Response({"error": "No assignments provided."}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        success_count = 0
        
        # Close existing connections to prevent database locks
        from django.db import connections
        for conn in connections.all():
            conn.close_if_unusable_or_obsolete()
        
        # Process in smaller batches to reduce lock contention
        batch_size = 10
        for i in range(0, len(assignments), batch_size):
            batch = assignments[i:i+batch_size]
            batch_results, batch_success_count = self._process_batch(batch)
            results.extend(batch_results)
            success_count += batch_success_count
        
        if success_count == 0:
            status_code = status.HTTP_400_BAD_REQUEST
        elif success_count == len(assignments):
            status_code = status.HTTP_201_CREATED
        else:
            status_code = status.HTTP_207_MULTI_STATUS
        
        return Response(
            {
                "results": results,
                "success_count": success_count,
                "total_operations": len(assignments)
            },
            status=status_code
        )
    
    def _process_batch(self, batch):
        results = []
        success_count = 0
        
        for assignment in batch:
            teacher_id = assignment.get('teacher_id')
            slot_id = assignment.get('slot_id')
            day_of_week = assignment.get('day_of_week')
            action = assignment.get('action', 'create').lower()
            
            result = {
                "action": action,
                "teacher_id": teacher_id,
                "slot_id": slot_id,
                "day_of_week": day_of_week,
                "success": False
            }
            
            # Skip if missing required fields
            if not all([teacher_id, slot_id, day_of_week is not None]):
                result["error"] = "Missing required fields: teacher_id, slot_id, or day_of_week"
                results.append(result)
                continue
            
            try:
                # Use a separate transaction for each assignment to prevent lock issues
                with transaction.atomic():
                    # Fetch teacher and slot
                    try:
                        teacher = Teacher.objects.get(id=teacher_id)
                    except Teacher.DoesNotExist:
                        raise DRFValidationError(f"Teacher with id {teacher_id} does not exist.")
                    
                    try:
                        slot = Slot.objects.get(pk=slot_id)
                    except Slot.DoesNotExist:
                        raise DRFValidationError(f"Slot with id {slot_id} does not exist.")
                    
                    if action in ['create', 'update']:
                        # Check 5-day week constraint
                        current_days = TeacherSlotAssignment.objects.filter(
                            teacher=teacher
                        ).values_list('day_of_week', flat=True).distinct()
                        
                        if len(current_days) >= 5 and day_of_week not in current_days:
                            raise DRFValidationError("Teacher already has assignments for 5 days. Maximum is 5 days per week.")
                        
                        # Check Monday/Saturday constraint - only one of these days allowed
                        if day_of_week in TeacherSlotAssignment.RESTRICTED_DAYS:
                            restricted_day_assignments = TeacherSlotAssignment.objects.filter(
                                teacher=teacher,
                                day_of_week__in=TeacherSlotAssignment.RESTRICTED_DAYS
                            ).exclude(day_of_week=day_of_week)
                            
                            if restricted_day_assignments.exists():
                                restricted_day = dict(TeacherSlotAssignment.DAYS_OF_WEEK)[restricted_day_assignments.first().day_of_week]
                                raise DRFValidationError(
                                    f"Teacher already has a slot assigned for {restricted_day}. "
                                    f"Teachers can only choose one of these days: Monday or Saturday."
                                )
                        
                        # Check slot type distribution constraint
                        # Get all current assignments for this teacher
                        current_assignments = list(TeacherSlotAssignment.objects.filter(
                            teacher=teacher
                        ).exclude(day_of_week=day_of_week).values_list('slot__slot_type', flat=True))
                        
                        # Add the new slot type to the distribution
                        current_assignments.append(slot.slot_type)
                        
                        # Count occurrences of each slot type
                        slot_type_counts = Counter(current_assignments)
                        total_assignments = len(current_assignments)
                        
                        # Don't need to check if less than 5 assignments
                        if total_assignments > 5:
                            raise DRFValidationError("Teacher cannot have more than 5 slot assignments in total.")
                        
                        # When we reach 5 assignments, ensure we have a valid combination
                        if total_assignments == 5:
                            # Valid combinations
                            valid_combinations = [
                                # Format: {A: count, B: count, C: count}
                                {'A': 2, 'B': 2, 'C': 1},
                                {'A': 1, 'B': 2, 'C': 2},
                                {'A': 2, 'B': 1, 'C': 2}
                            ]
                            
                            is_valid = False
                            for combo in valid_combinations:
                                if all(slot_type_counts.get(slot_type, 0) == count for slot_type, count in combo.items()):
                                    is_valid = True
                                    break
                            
                            if not is_valid:
                                slot_a_count = slot_type_counts.get('A', 0)
                                slot_b_count = slot_type_counts.get('B', 0)
                                slot_c_count = slot_type_counts.get('C', 0)
                                
                                raise DRFValidationError(
                                    f"Invalid slot distribution. Current distribution is: "
                                    f"A: {slot_a_count}, B: {slot_b_count}, C: {slot_c_count}. "
                                    f"Valid distributions for 5 days are: A-2/B-2/C-1, A-1/B-2/C-2, or A-2/B-1/C-2."
                                )
                        
                        # Check department distribution constraint (33% per slot type)
                        if teacher.dept_id:
                            dept_id = teacher.dept_id.id
                            total_dept_teachers = Teacher.objects.filter(dept_id=dept_id).count()
                            
                            if total_dept_teachers > 0:
                                # Get count of teachers in this department assigned to this slot type on this day
                                teachers_in_slot = TeacherSlotAssignment.objects.filter(
                                    teacher__dept_id=dept_id,
                                    day_of_week=day_of_week,
                                    slot__slot_type=slot.slot_type
                                ).values('teacher').distinct().count()
                                
                                # Calculate max teachers allowed (33% of department + 1 extra teacher)
                                max_teachers_per_slot = int((total_dept_teachers * 0.33) + 0.5) + 1  # Adding 1 to allow one extra teacher
                                
                                if teachers_in_slot >= max_teachers_per_slot:
                                    raise DRFValidationError(
                                        f"Maximum number of teachers (33% + 1) from department {teacher.dept_id.dept_name} "
                                        f"already assigned to slot type {slot.slot_type} on {dict(TeacherSlotAssignment.DAYS_OF_WEEK)[day_of_week]}."
                                    )
                        
                        # Create or update assignment
                        assignment_obj, created = TeacherSlotAssignment.objects.get_or_create(
                            teacher=teacher,
                            day_of_week=day_of_week,
                            defaults={'slot': slot}
                        )
                        
                        if not created:
                            assignment_obj.slot = slot
                            assignment_obj.full_clean()
                            assignment_obj.save()
                            result["message"] = "Slot assignment updated successfully."
                        else:
                            result["message"] = "Slot assignment created successfully."
                        
                        result["success"] = True
                        success_count += 1
                    elif action == 'delete':
                        try:
                            assignment_obj = TeacherSlotAssignment.objects.get(
                                teacher=teacher,
                                day_of_week=day_of_week
                            )
                            assignment_obj.delete()
                            result["message"] = "Slot assignment deleted successfully."
                            result["success"] = True
                            success_count += 1
                        except TeacherSlotAssignment.DoesNotExist:
                            raise DRFValidationError("Slot assignment not found.")
                    else:
                        raise DRFValidationError(f"Invalid action: {action}")
            
            except (ValidationError, DRFValidationError) as e:
                if hasattr(e, 'message_dict'):
                    result["error"] = e.message_dict
                elif hasattr(e, 'detail'):
                    # Handle DRF validation errors which have a detail attribute
                    if isinstance(e.detail, list) and len(e.detail) > 0:
                        # If it's a list of error details, get the first one
                        error_detail = e.detail[0]
                        if hasattr(error_detail, 'string'):
                            # Direct access to the string representation
                            result["error"] = error_detail.string
                        else:
                            # Fallback to str representation
                            result["error"] = str(error_detail)
                    else:
                        # Otherwise, convert the detail to string
                        result["error"] = str(e.detail)
                else:
                    # Regular string errors
                    result["error"] = str(e)
            except Exception as e:
                result["error"] = str(e)
            
            results.append(result)
        
        return results, success_count