from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from datetime import date

from .models import Timetable, TimetableChange, TimetableGenerationConfig
from .serializers import (
    TimetableSerializer, TimetableWriteSerializer, 
    TimetableChangeSerializer, TimetableGenerationConfigSerializer
)
from .services import TimetableGenerationService
from teacherCourse.models import TeacherCourse
from slot.models import Slot
from rooms.models import Room

class TimetableViewSet(viewsets.ModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TimetableWriteSerializer
        return TimetableSerializer
    
    def get_queryset(self):
        queryset = Timetable.objects.all()
        
        # Filter by course_id
        course_id = self.request.query_params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_assignment__course_id=course_id)
        
        # Filter by teacher_id
        teacher_id = self.request.query_params.get('teacher_id')
        if teacher_id:
            queryset = queryset.filter(course_assignment__teacher_id=teacher_id)
        
        # Filter by day_of_week
        day_of_week = self.request.query_params.get('day_of_week')
        if day_of_week:
            queryset = queryset.filter(day_of_week=day_of_week)
        
        # Filter by room_id
        room_id = self.request.query_params.get('room_id')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        # Filter by slot_id
        slot_id = self.request.query_params.get('slot_id')
        if slot_id:
            queryset = queryset.filter(slot_id=slot_id)
        
        # Filter by student's batch, semester, department
        student_batch = self.request.query_params.get('student_batch')
        semester = self.request.query_params.get('semester')
        dept_id = self.request.query_params.get('dept_id')
        
        if student_batch or semester or dept_id:
            filters = Q()
            if student_batch:
                filters &= Q(course_assignment__course_id__student_batch=student_batch)
            if semester:
                filters &= Q(course_assignment__course_id__course_semester=semester)
            if dept_id:
                filters &= Q(course_assignment__course_id__for_dept_id=dept_id)
            
            queryset = queryset.filter(filters)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def teacher_timetable(self, request):
        """Get timetable for a specific teacher"""
        teacher_id = request.query_params.get('teacher_id')
        if not teacher_id:
            return Response({"error": "teacher_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        timetable = Timetable.objects.filter(course_assignment__teacher_id=teacher_id)
        serializer = self.get_serializer(timetable, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def student_timetable(self, request):
        """Get timetable for a specific student based on their courses"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({"error": "student_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the student's courses
        from studentCourse.models import StudentCourse
        student_courses = StudentCourse.objects.filter(student_id=student_id).values_list('course_id', flat=True)
        
        # Get timetable entries for these courses
        timetable = Timetable.objects.filter(course_assignment__course_id__in=student_courses)
        serializer = self.get_serializer(timetable, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def check_availability(self, request):
        """Check if a slot is available for a room on a specific day"""
        room_id = request.query_params.get('room_id')
        slot_id = request.query_params.get('slot_id')
        day_of_week = request.query_params.get('day_of_week')
        
        if not all([room_id, slot_id, day_of_week]):
            return Response(
                {"error": "room_id, slot_id, and day_of_week parameters are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if timetable entry exists
        is_booked = Timetable.objects.filter(
            room_id=room_id,
            slot_id=slot_id,
            day_of_week=day_of_week
        ).exists()
        
        return Response({"is_available": not is_booked})


class TimetableChangeViewSet(viewsets.ModelViewSet):
    queryset = TimetableChange.objects.all()
    serializer_class = TimetableChangeSerializer
    
    def get_queryset(self):
        queryset = TimetableChange.objects.all()
        
        # Filter by timetable_id
        timetable_id = self.request.query_params.get('timetable_id')
        if timetable_id:
            queryset = queryset.filter(original_timetable=timetable_id)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by date range
        effective_from = self.request.query_params.get('effective_from')
        effective_to = self.request.query_params.get('effective_to')
        
        if effective_from:
            queryset = queryset.filter(effective_from__gte=effective_from)
        if effective_to:
            queryset = queryset.filter(effective_to__lte=effective_to)
        
        # Get active changes (based on current date)
        is_active = self.request.query_params.get('is_active')
        if is_active and is_active.lower() == 'true':
            today = date.today()
            # Fix: Combine Q objects first, then pass as a single filter argument
            date_filter = Q(effective_from__lte=today) & (Q(effective_to__gte=today) | Q(effective_to__isnull=True))
            queryset = queryset.filter(date_filter)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        # Ensure created_by is set to the current user
        if not request.data.get('created_by'):
            request.data['created_by'] = request.user.pk
            
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a timetable change request"""
        timetable_change = self.get_object()
        if timetable_change.status != 'Pending':
            return Response(
                {"error": "Only pending changes can be approved"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        timetable_change.status = 'Approved'
        timetable_change.save()
        return Response({"status": "approved"})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a timetable change request"""
        timetable_change = self.get_object()
        if timetable_change.status != 'Pending':
            return Response(
                {"error": "Only pending changes can be rejected"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        timetable_change.status = 'Rejected'
        timetable_change.save()
        return Response({"status": "rejected"})


class TimetableGenerationViewSet(viewsets.ModelViewSet):
    """ViewSet for timetable generation using OR-Tools"""
    queryset = TimetableGenerationConfig.objects.all()
    serializer_class = TimetableGenerationConfigSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generate timetable using OR-Tools"""
        config = self.get_object()
        
        # Check if already generated
        if config.is_generated:
            return Response(
                {"error": "Timetable has already been generated with this configuration"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate timetable
        service = TimetableGenerationService(config_id=pk)
        success = service.generate_timetable()
        
        if success:
            return Response({"status": "success", "message": "Timetable generated successfully"})
        else:
            return Response(
                {"status": "error", "message": "Failed to generate timetable", "log": config.generation_log},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get status of all timetable generation configs"""
        configs = TimetableGenerationConfig.objects.all().order_by('-created_at')
        
        results = []
        for config in configs:
            results.append({
                "id": config.id,
                "name": config.name,
                "is_generated": config.is_generated,
                "created_at": config.created_at,
                "generated_at": config.generation_completed_at,
                "created_by": config.created_by.username
            })
        
        return Response(results)
    
    @action(detail=True, methods=['get'])
    def get_log(self, request, pk=None):
        """Get generation log for a specific config"""
        config = self.get_object()
        
        return Response({
            "id": config.id,
            "name": config.name,
            "is_generated": config.is_generated,
            "created_at": config.created_at,
            "started_at": config.generation_started_at,
            "completed_at": config.generation_completed_at,
            "log": config.generation_log
        })
