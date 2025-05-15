from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from datetime import date, datetime, timedelta

from .models import Attendance, AttendanceSession
from .serializers import (
    AttendanceSerializer, AttendanceWriteSerializer,
    AttendanceSessionSerializer, AttendanceSessionWriteSerializer,
    BulkAttendanceSerializer
)
from student.models import Student
from teacher.models import Teacher
from timetable.models import Timetable

class AttendanceSessionViewSet(viewsets.ModelViewSet):
    queryset = AttendanceSession.objects.all()
    serializer_class = AttendanceSessionSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AttendanceSessionWriteSerializer
        return AttendanceSessionSerializer
    
    def get_queryset(self):
        queryset = AttendanceSession.objects.all()
        
        # Filter by timetable_slot
        timetable_slot = self.request.query_params.get('timetable_slot')
        if timetable_slot:
            queryset = queryset.filter(timetable_slot=timetable_slot)
        
        # Filter by date
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(date=date_param)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by teacher
        teacher_id = self.request.query_params.get('teacher_id')
        if teacher_id:
            queryset = queryset.filter(
                Q(conducted_by=teacher_id) | Q(substitute_teacher=teacher_id)
            )
        
        # Filter by course
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(timetable_slot__course_assignment__course_id=course_id)
        
        # Date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get attendance sessions for today"""
        today_date = date.today()
        sessions = AttendanceSession.objects.filter(date=today_date)
        
        # Filter by teacher if specified
        teacher_id = request.query_params.get('teacher_id')
        if teacher_id:
            sessions = sessions.filter(
                Q(conducted_by=teacher_id) | Q(substitute_teacher=teacher_id)
            )
        
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get attendance sessions for the current week"""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)  # Sunday
        
        sessions = AttendanceSession.objects.filter(
            date__gte=start_of_week,
            date__lte=end_of_week
        )
        
        # Filter by teacher if specified
        teacher_id = request.query_params.get('teacher_id')
        if teacher_id:
            sessions = sessions.filter(
                Q(conducted_by=teacher_id) | Q(substitute_teacher=teacher_id)
            )
        
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AttendanceWriteSerializer
        return AttendanceSerializer
    
    def get_queryset(self):
        queryset = Attendance.objects.all()
        
        # Filter by student
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student=student_id)
        
        # Filter by timetable_slot
        timetable_slot = self.request.query_params.get('timetable_slot')
        if timetable_slot:
            queryset = queryset.filter(timetable_slot=timetable_slot)
        
        # Filter by date
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(date=date_param)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by course
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(timetable_slot__course_assignment__course_id=course_id)
        
        # Date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create attendance records for multiple students in a single session"""
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        timetable_slot_id = data['timetable_slot_id']
        attendance_date = data['date']
        marked_by_id = data['marked_by_id']
        attendance_data = data['attendance_data']
        
        try:
            timetable_slot = Timetable.objects.get(pk=timetable_slot_id)
            teacher = Teacher.objects.get(pk=marked_by_id)
            
            # Create or update session record
            session, created = AttendanceSession.objects.get_or_create(
                timetable_slot=timetable_slot,
                date=attendance_date,
                defaults={
                    'status': 'Completed',
                    'conducted_by': teacher
                }
            )
            
            # Process attendance records
            with transaction.atomic():
                created_count = 0
                updated_count = 0
                
                for record in attendance_data:
                    student_id = record['student_id']
                    status = record['status']
                    remarks = record.get('remarks', '')
                    
                    student = Student.objects.get(pk=student_id)
                    
                    # Update or create attendance record
                    attendance, created = Attendance.objects.update_or_create(
                        student=student,
                        timetable_slot=timetable_slot,
                        date=attendance_date,
                        defaults={
                            'status': status,
                            'remarks': remarks,
                            'marked_by': teacher,
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
            
            return Response({
                'success': True,
                'message': f'Created {created_count} and updated {updated_count} attendance records.',
                'session_id': session.id
            }, status=status.HTTP_201_CREATED)
            
        except (Timetable.DoesNotExist, Teacher.DoesNotExist, Student.DoesNotExist) as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def student_attendance(self, request):
        """Get attendance for a specific student"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({"error": "student_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        attendance = self.get_queryset().filter(student=student_id)
        
        # Course filtering
        course_id = request.query_params.get('course_id')
        if course_id:
            attendance = attendance.filter(timetable_slot__course_assignment__course_id=course_id)
        
        serializer = self.get_serializer(attendance, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def course_attendance_stats(self, request):
        """Get attendance statistics for a course"""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({"error": "course_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all attendance for this course
        attendance = Attendance.objects.filter(
            timetable_slot__course_assignment__course_id=course_id
        )
        
        # Calculate statistics
        total_sessions = AttendanceSession.objects.filter(
            timetable_slot__course_assignment__course_id=course_id
        ).count()
        
        # Get student count
        student_count = attendance.values('student').distinct().count()
        
        # Get attendance by status
        status_counts = attendance.values('status').annotate(count=Count('id'))
        
        # Calculate attendance percentage
        present_count = attendance.filter(status='Present').count()
        total_count = attendance.count()
        attendance_percentage = (present_count / total_count * 100) if total_count > 0 else 0
        
        return Response({
            'course_id': course_id,
            'total_sessions': total_sessions,
            'student_count': student_count,
            'status_counts': status_counts,
            'attendance_percentage': attendance_percentage
        })
