from django.shortcuts import render
from rest_framework import generics, permissions, status, serializers, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from authentication.authentication import IsAuthenticated, CustomIsAuthenticated
from .models import StudentCourse, StudentCoursePreference
from .serializers import StudentCourseSerializer, StudentCoursePreferenceSerializer
from department.models import Department
from utlis.pagination import PagePagination
from django.db.models import Q, Sum
from course.models import Course
from teacher.models import Teacher
from teacherCourse.models import TeacherCourse
from slot.models import Slot
from timetable.models import Timetable, TimetableChange
from django.utils import timezone
from datetime import datetime
import logging

# Create your views here.
class StudentCourseListCreateView(generics.ListCreateAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [CustomIsAuthenticated]
    serializer_class = StudentCourseSerializer
    pagination_class = PagePagination

    def get_queryset(self):
        user = self.request.user
        
        try:
            hod_dept = Department.objects.get(hod_id=user)
            return StudentCourse.objects.filter(
                student_id__dept_id=hod_dept,
                course_id__for_dept_id=hod_dept
            )
        except Department.DoesNotExist:
            return StudentCourse.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        try:
            hod_dept = Department.objects.get(hod_id=user)
            student = serializer.validated_data['student_id']
            course = serializer.validated_data['course_id']
            
            if student.dept_id != hod_dept:
                raise serializers.ValidationError(
                    "Only HOD can create student course enrollments"
                )
                
            serializer.save()
        except Department.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Only HOD can create student course enrollments."}
            )

class StudentCourseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [CustomIsAuthenticated]
    serializer_class = StudentCourseSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        
        try:
            hod_dept = Department.objects.get(hod_id=user)
            return StudentCourse.objects.filter(
                student_id__dept_id=hod_dept,
                course_id__for_dept_id=hod_dept
            )
        except Department.DoesNotExist:
            return StudentCourse.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        try:
            hod_dept = Department.objects.get(hod_id=user)
            instance = self.get_object()
            
            serializer.save()
        except Department.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Only HOD can update student course enrollments."}
            )

class StudentCourseViewSet(viewsets.ModelViewSet):
    serializer_class = StudentCourseSerializer
    authentication_classes = [IsAuthenticated]
    permission_classes = [CustomIsAuthenticated]

    def get_queryset(self):
        # If student, show only their courses
        if self.request.user.user_type == 'student':
            return StudentCourse.objects.filter(
                student_id__student_id=self.request.user
            ).select_related(
                'student_id', 'course_id', 'teacher_id', 'slot_id'
            )
        # If staff/admin, show all
        return StudentCourse.objects.all().select_related(
            'student_id', 'course_id', 'teacher_id', 'slot_id'
        )

    @action(detail=False, methods=['GET'])
    def available_courses(self, request):
        """Get courses available for the student's department and semester"""
        if request.user.user_type != 'student':
            return Response(
                {"detail": "Only students can view available courses"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            logger = logging.getLogger('django')
            logger.info(f"User {request.user.id} requested available_courses")
            
            # Get student profile
            student = None
            if hasattr(request.user, 'student_profile'):
                student = request.user.student_profile.first()
                
            if not student:
                logger.warning(f"No student profile found for user {request.user.id}")
                return Response(
                    {"detail": "Student profile not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if student has dept_id and current_semester
            has_dept = hasattr(student, 'dept_id') and student.dept_id is not None
            has_semester = hasattr(student, 'current_semester') and student.current_semester is not None
            
            if not has_dept:
                logger.warning(f"Student {student.id} missing department")
                return Response(
                    {"detail": "Your student profile is not associated with a department"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if not has_semester:
                logger.warning(f"Student {student.id} missing current semester")
                return Response(
                    {"detail": "Your student profile does not have a current semester set"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            logger.info(f"Getting courses for dept_id={student.dept_id.id}, semester={student.current_semester}")

            # Get courses for student's department and semester
            courses = Course.objects.filter(
                for_dept_id=student.dept_id,
                course_semester=student.current_semester
            ).select_related('course_id', 'for_dept_id', 'teaching_dept_id')
            
            logger.info(f"Found {courses.count()} courses for student")

            from course.serializers import StudentCourseListSerializer
            serialized_data = StudentCourseListSerializer(courses, many=True).data
            return Response(serialized_data)
        except Exception as e:
            # Log the error
            logger = logging.getLogger('django')
            logger.error(f"Error in available_courses: {str(e)}", exc_info=True)
            
            return Response({
                "error": "An error occurred while retrieving courses",
                "detail": str(e),
                "courses": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def available_courses_all(self, request):
        """Get all available courses for students regardless of department"""
        try:
            logger = logging.getLogger('django')
            logger.info(f"User {request.user.id} requested available_courses_all")
            
            # Get all courses
            courses = Course.objects.all().select_related(
                'course_id', 'for_dept_id', 'teaching_dept_id'
            )
            
            logger.info(f"Found {courses.count()} courses total")

            from course.serializers import StudentCourseListSerializer
            serialized_data = StudentCourseListSerializer(courses, many=True).data
            logger.info(f"Serialized {len(serialized_data)} courses")
            
            return Response(serialized_data)
        except Exception as e:
            logger = logging.getLogger('django')
            logger.error(f"Error in available_courses_all: {str(e)}", exc_info=True)
            
            # Return empty list with error message
            return Response({
                "error": "An error occurred while retrieving courses",
                "detail": str(e),
                "courses": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], authentication_classes=[], permission_classes=[])
    def filtered_courses(self, request):
        """Endpoint that allows filtering courses by department and semester with validation"""
        try:
            logger = logging.getLogger('django')
            logger.info("Filtered courses endpoint called")
            
            # Get filter parameters
            department_id = request.query_params.get('department_id')
            semester = request.query_params.get('semester')
            year = request.query_params.get('year')
            
            # Require at least one filter parameter
            if not department_id and not semester and not year:
                return Response(
                    {"detail": "At least one filter parameter (department_id, semester, or year) is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Start with all courses
            courses_query = Course.objects.all()
            
            # Apply filters if provided
            if department_id:
                try:
                    dept_id = int(department_id)
                    logger.info(f"Filtering by department_id={dept_id}")
                    courses_query = courses_query.filter(for_dept_id=dept_id)
                except ValueError:
                    return Response(
                        {"detail": "department_id must be a valid integer"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            if semester:
                try:
                    sem = int(semester)
                    logger.info(f"Filtering by semester={sem}")
                    courses_query = courses_query.filter(course_semester=sem)
                except ValueError:
                    return Response(
                        {"detail": "semester must be a valid integer"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            if year:
                try:
                    yr = int(year)
                    logger.info(f"Filtering by year={yr}")
                    courses_query = courses_query.filter(course_year=yr)
                except ValueError:
                    return Response(
                        {"detail": "year must be a valid integer"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Get the filtered courses with related objects
            courses = courses_query.select_related(
                'course_id', 'for_dept_id', 'teaching_dept_id'
            )
            
            logger.info(f"Found {courses.count()} courses total after filtering")

            from course.serializers import StudentCourseListSerializer
            serialized_data = StudentCourseListSerializer(courses, many=True).data
            logger.info(f"Serialized {len(serialized_data)} courses")
            
            return Response(serialized_data)
        except Exception as e:
            logger = logging.getLogger('django')
            logger.error(f"Error in filtered_courses: {str(e)}", exc_info=True)
            
            # Return empty list with error message
            return Response({
                "error": "An error occurred while retrieving courses",
                "detail": str(e),
                "courses": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def dashboard(self, request):
        """Get dashboard data for the student"""
        if request.user.user_type != 'student':
            return Response(
                {"detail": "Only students can view their dashboard"},
                status=status.HTTP_403_FORBIDDEN
            )

        student = request.user.student_profile.first()
        if not student:
            return Response(
                {"detail": "Student profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get enrolled courses data
        enrolled_courses = StudentCourse.objects.filter(
            student_id__student_id=request.user
        ).select_related('course_id')
        
        # Count of enrolled courses
        enrolled_count = enrolled_courses.count()
        
        # Calculate total credits
        total_credits = enrolled_courses.aggregate(
            total=Sum('course_id__credits')
        )['total'] or 0
        
        # Calculate class hours per week
        class_hours = enrolled_courses.aggregate(
            total=Sum('course_id__weekly_hours')
        )['total'] or 0
        
        # If weekly hours not available, estimate from credits
        if class_hours == 0:
            class_hours = total_credits * 1.5  # Estimate 1.5 hours per credit
            
        # Get today's schedule
        today = timezone.now().strftime('%A').lower()
        today_classes = enrolled_courses.filter(
            slot_id__day_of_week=today
        ).select_related('course_id', 'teacher_id', 'slot_id')
        
        # Format today's schedule
        today_schedule = []
        for course in today_classes:
            today_schedule.append({
                'id': course.id,
                'course': {
                    'id': course.course_id.id,
                    'code': course.course_id.course_code,
                    'name': course.course_id.course_name
                },
                'teacher': {
                    'id': course.teacher_id.id if course.teacher_id else None,
                    'name': course.teacher_id.teacher_id.get_full_name() if course.teacher_id else 'TBA'
                },
                'startTime': course.slot_id.start_time.strftime('%H:%M') if course.slot_id.start_time else None,
                'endTime': course.slot_id.end_time.strftime('%H:%M') if course.slot_id.end_time else None,
                'room': course.room_id.room_name if hasattr(course, 'room_id') and course.room_id else 'TBA'
            })
        
        dashboard_data = {
            'enrolledCourses': enrolled_count,
            'totalCredits': total_credits,
            'classHours': class_hours,
            'todaySchedule': today_schedule
        }
        
        return Response(dashboard_data)

    @action(detail=False, methods=['GET'])
    def available_teachers(self, request):
        """Get available teachers for a specific course"""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {"detail": "course_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            logger = logging.getLogger('django')
            logger.info(f"Available teachers requested for course_id={course_id}")
            
            # Verify the course exists
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                return Response(
                    {"detail": f"Course with id {course_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # If user is a student, verify they should have access to this course
            if request.user.user_type == 'student':
                student = request.user.student_profile.first()
                if student and student.dept_id and course.for_dept_id:
                    # Check if course is for student's department and semester
                    if student.dept_id.id != course.for_dept_id.id:
                        logger.warning(f"Student from dept {student.dept_id.id} attempted to access course for dept {course.for_dept_id.id}")
                        return Response(
                            {"detail": "You do not have access to this course's teachers"},
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            # Get teachers assigned to this course through TeacherCourse
            teachers = Teacher.objects.filter(
                teachercourse__course_id=course_id
            ).select_related('teacher_id')

            from teacher.serializers import TeacherSerializer
            return Response(TeacherSerializer(teachers, many=True).data)
        except Exception as e:
            logger.error(f"Error in available_teachers: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An error occurred while retrieving teachers"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'])
    def available_slots(self, request):
        """Get available slots for a teacher and course from the timetable"""
        course_id = request.query_params.get('course_id')
        teacher_id = request.query_params.get('teacher_id')

        if not course_id or not teacher_id:
            return Response(
                {"detail": "Both course_id and teacher_id parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            logger = logging.getLogger('django')
            logger.info(f"Available slots requested for course_id={course_id}, teacher_id={teacher_id}")
            
            # Validate parameters
            try:
                course_id_int = int(course_id)
                teacher_id_int = int(teacher_id)
            except ValueError:
                return Response(
                    {"detail": "course_id and teacher_id must be valid integers"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verify the course exists
            try:
                course = Course.objects.get(id=course_id_int)
            except Course.DoesNotExist:
                return Response(
                    {"detail": f"Course with id {course_id_int} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Verify the teacher exists
            try:
                teacher = Teacher.objects.get(id=teacher_id_int)
            except Teacher.DoesNotExist:
                return Response(
                    {"detail": f"Teacher with id {teacher_id_int} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # If user is a student, verify they should have access to this course
            if request.user.user_type == 'student':
                student = request.user.student_profile.first()
                if student and student.dept_id and course.for_dept_id:
                    # Check if course is for student's department and semester
                    if student.dept_id.id != course.for_dept_id.id:
                        logger.warning(f"Student from dept {student.dept_id.id} attempted to access course for dept {course.for_dept_id.id}")
                        return Response(
                            {"detail": "You do not have access to this course's slots"},
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            # Get the TeacherCourse assignment
            teacher_course = TeacherCourse.objects.filter(
                teacher_id=teacher_id_int,
                course_id=course_id_int
            ).first()
            
            if not teacher_course:
                return Response(
                    {"detail": "This teacher is not assigned to the specified course"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # First check if there's an OR-Tools-generated timetable for this teacher-course
            # Get slots from the timetable where this teacher-course is assigned
            timetable_entries = Timetable.objects.filter(
                course_assignment=teacher_course
            ).select_related('slot', 'room')
            
            if timetable_entries.exists():
                logger.info(f"Found OR-Tools-generated timetable entries for teacher {teacher_id_int} and course {course_id_int}")
                
                # Format the response with timetable entries
                timetable_data = []
                for entry in timetable_entries:
                    timetable_data.append({
                        "id": entry.slot.id,
                        "slot_name": entry.slot.slot_name,
                        "day_of_week": entry.get_day_of_week_display(),
                        "start_time": entry.slot.start_time.strftime('%H:%M') if entry.slot.start_time else None,
                        "end_time": entry.slot.end_time.strftime('%H:%M') if entry.slot.end_time else None,
                        "room": {
                            "id": entry.room.id,
                            "room_number": entry.room.room_number,
                            "room_name": entry.room.room_name
                        },
                        "is_from_timetable": True,
                        "course_assignment": entry.course_assignment.id
                    })
                
                # Check if slots are already assigned to this student for other courses
                if request.user.user_type == 'student':
                    student = request.user.student_profile.first()
                    if student:
                        # Get slots already assigned to this student
                        occupied_slot_ids = StudentCourse.objects.filter(
                            student_id=student,
                            status='approved'
                        ).exclude(
                            course_id=course_id_int  # Exclude current course
                        ).values_list('slot_id', flat=True)
                        
                        # Filter out any timetable entries with conflicting slots
                        timetable_data = [entry for entry in timetable_data 
                                          if entry["id"] not in occupied_slot_ids]
                
                return Response(timetable_data)
            else:
                logger.warning(f"No OR-Tools-generated timetable entries found for teacher {teacher_id_int} and course {course_id_int}")
                
                # Fallback to regular slots if no timetable entries found
                all_slots = Slot.objects.all()
                
                # Get slots where teacher is already assigned
                occupied_slots = StudentCourse.objects.filter(
                    teacher_id=teacher_id_int,
                    status='approved'
                ).exclude(
                    course_id=course_id_int  # Exclude current course
                ).values_list('slot_id', flat=True)
                
                # Filter out occupied slots
                available_slots = all_slots.exclude(id__in=occupied_slots)
                
                # Check if slots are already assigned to this student for other courses
                if request.user.user_type == 'student':
                    student = request.user.student_profile.first()
                    if student:
                        # Get slots already assigned to this student
                        student_occupied_slots = StudentCourse.objects.filter(
                            student_id=student,
                            status='approved'
                        ).exclude(
                            course_id=course_id_int  # Exclude current course
                        ).values_list('slot_id', flat=True)
                        
                        # Filter out slots that are occupied by the student
                        available_slots = available_slots.exclude(id__in=student_occupied_slots)
                
                from slot.serializers import SlotSerializer
                slots_data = SlotSerializer(available_slots, many=True).data
                
                # Mark these slots as not from timetable
                for slot_data in slots_data:
                    slot_data['is_from_timetable'] = False
                    
                logger.info(f"Returning {len(slots_data)} regular slots as fallback")
                
                # Return with a warning
                return Response({
                    "warning": "No timetable entries found for this teacher-course combination. Showing regular available slots instead.",
                    "slots": slots_data
                })
                
        except Exception as e:
            logger.error(f"Error in available_slots: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An error occurred while retrieving available slots"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['POST'])
    def add_teacher_preference(self, request, pk=None):
        """Add a teacher preference for a course selection"""
        student_course = self.get_object()
        teacher_id = request.data.get('teacher_id')
        preference_order = request.data.get('preference_order')

        if not teacher_id or preference_order is None:
            return Response(
                {"detail": "teacher_id and preference_order are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or update preference
        preference, created = StudentCoursePreference.objects.update_or_create(
            student_course=student_course,
            teacher_id_id=teacher_id,
            defaults={'preference_order': preference_order}
        )

        return Response(
            StudentCoursePreferenceSerializer(preference).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        # Automatically set student if request is from student
        if self.request.user.user_type == 'student':
            student = self.request.user.student_profile.first()
            if student:
                serializer.save(student_id=student)
            else:
                raise ValidationError("Student profile not found")
        else:
            serializer.save()

    @action(detail=False, methods=['GET'])
    def debug_info(self, request):
        """Debug endpoint to check student profile information"""
        user_info = {
            'user_id': request.user.id,
            'username': request.user.username,
            'is_authenticated': request.user.is_authenticated,
            'user_type': getattr(request.user, 'user_type', 'unknown'),
        }
        
        student_info = {}
        try:
            # Try to get student profile
            student = None
            if hasattr(request.user, 'student_profile'):
                student = request.user.student_profile.first()
            
            if student:
                student_info = {
                    'student_id': student.id,
                    'has_dept': hasattr(student, 'dept_id'),
                    'dept_id': getattr(student, 'dept_id', None) and student.dept_id.id if hasattr(student, 'dept_id') else None,
                    'dept_name': getattr(student, 'dept_id', None) and student.dept_id.dept_name if hasattr(student, 'dept_id') and student.dept_id else None,
                    'has_semester': hasattr(student, 'current_semester'),
                    'current_semester': getattr(student, 'current_semester', None),
                }
        except Exception as e:
            student_info = {'error': str(e)}
        
        # Course counts
        course_counts = {
            'all_courses': Course.objects.count(),
        }
        
        if 'dept_id' in student_info and student_info['dept_id']:
            course_counts['dept_courses'] = Course.objects.filter(for_dept_id_id=student_info['dept_id']).count()
            
            if 'current_semester' in student_info and student_info['current_semester']:
                course_counts['dept_semester_courses'] = Course.objects.filter(
                    for_dept_id_id=student_info['dept_id'],
                    course_semester=student_info['current_semester']
                ).count()
        
        return Response({
            'user': user_info,
            'student': student_info,
            'course_counts': course_counts,
            'request_info': {
                'path': request.path,
                'method': request.method,
                'headers': dict(request.headers),
                'query_params': dict(request.query_params),
            }
        })

    @action(detail=False, methods=['GET'], authentication_classes=[], permission_classes=[])
    def filtered_slots(self, request):
        """Endpoint to get available slots for a teacher and course from teacher timetable"""
        course_id = request.query_params.get('course_id')
        teacher_id = request.query_params.get('teacher_id')

        if not course_id or not teacher_id:
            return Response(
                {"detail": "Both course_id and teacher_id parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            logger = logging.getLogger('django')
            logger.info(f"Filtered slots endpoint called for course_id={course_id}, teacher_id={teacher_id}")
            
            # Validate parameters
            try:
                course_id_int = int(course_id)
                teacher_id_int = int(teacher_id)
            except ValueError:
                return Response(
                    {"detail": "course_id and teacher_id must be valid integers"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Get the TeacherCourse assignment
            teacher_course = TeacherCourse.objects.filter(
                teacher_id=teacher_id_int,
                course_id=course_id_int
            ).first()
            
            if not teacher_course:
                return Response(
                    {"detail": "This teacher is not assigned to the specified course"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # First check if there's an OR-Tools-generated timetable for this teacher-course
            # Get slots from the timetable where this teacher-course is assigned
            timetable_entries = Timetable.objects.filter(
                course_assignment=teacher_course
            ).select_related('slot', 'room')
            
            if timetable_entries.exists():
                logger.info(f"Found OR-Tools-generated timetable entries for teacher {teacher_id_int} and course {course_id_int}")
                
                # Format the response with timetable entries
                timetable_data = []
                for entry in timetable_entries:
                    timetable_data.append({
                        "id": entry.slot.id,
                        "slot_name": entry.slot.slot_name,
                        "day_of_week": entry.get_day_of_week_display(),
                        "start_time": entry.slot.start_time.strftime('%H:%M') if entry.slot.start_time else None,
                        "end_time": entry.slot.end_time.strftime('%H:%M') if entry.slot.end_time else None,
                        "room": {
                            "id": entry.room.id,
                            "room_number": entry.room.room_number,
                            "room_name": entry.room.room_name
                        },
                        "is_from_timetable": True,
                        "course_assignment": entry.course_assignment.id
                    })
                
                # Check if slots are already assigned to this student for other courses
                if hasattr(request, 'user') and request.user.is_authenticated and request.user.user_type == 'student':
                    student = request.user.student_profile.first()
                    if student:
                        # Get slots already assigned to this student
                        occupied_slot_ids = StudentCourse.objects.filter(
                            student_id=student,
                            status='approved'
                        ).exclude(
                            course_id=course_id_int  # Exclude current course
                        ).values_list('slot_id', flat=True)
                        
                        # Filter out any timetable entries with conflicting slots
                        timetable_data = [entry for entry in timetable_data 
                                          if entry["id"] not in occupied_slot_ids]
                
                return Response(timetable_data)
            else:
                logger.warning(f"No OR-Tools-generated timetable entries found for teacher {teacher_id_int} and course {course_id_int}")
                
                # Fallback to regular slots if no timetable entries found
                all_slots = Slot.objects.all()
                
                # Get slots where teacher is already assigned
                occupied_slots = StudentCourse.objects.filter(
                    teacher_id=teacher_id_int,
                    status='approved'
                ).exclude(
                    course_id=course_id_int  # Exclude current course
                ).values_list('slot_id', flat=True)
                
                # Filter out occupied slots
                available_slots = all_slots.exclude(id__in=occupied_slots)
                
                # Check if slots are already assigned to this student for other courses
                if hasattr(request, 'user') and request.user.is_authenticated and request.user.user_type == 'student':
                    student = request.user.student_profile.first()
                    if student:
                        # Get slots already assigned to this student
                        student_occupied_slots = StudentCourse.objects.filter(
                            student_id=student,
                            status='approved'
                        ).exclude(
                            course_id=course_id_int  # Exclude current course
                        ).values_list('slot_id', flat=True)
                        
                        # Filter out slots that are occupied by the student
                        available_slots = available_slots.exclude(id__in=student_occupied_slots)
                
                from slot.serializers import SlotSerializer
                slots_data = SlotSerializer(available_slots, many=True).data
                
                # Mark these slots as not from timetable
                for slot_data in slots_data:
                    slot_data['is_from_timetable'] = False
                    
                logger.info(f"Returning {len(slots_data)} regular slots as fallback")
                
                # Return with a warning
                return Response({
                    "warning": "No timetable entries found for this teacher-course combination. Showing regular available slots instead.",
                    "slots": slots_data
                })
            
        except Exception as e:
            logger = logging.getLogger('django')
            logger.error(f"Error in filtered_slots: {str(e)}", exc_info=True)
            
            return Response({
                "error": "An error occurred while retrieving available slots",
                "detail": str(e),
                "slots": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StudentCoursePreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = StudentCoursePreferenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.user_type == 'student':
            return StudentCoursePreference.objects.filter(
                student_course__student_id__student_id=self.request.user
            ).select_related('teacher_id', 'student_course')
        return StudentCoursePreference.objects.all().select_related(
            'teacher_id', 'student_course'
        )