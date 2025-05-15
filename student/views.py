from django.shortcuts import render
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.db.models import Count, Sum
from authentication.authentication import IsAuthenticated
from .models import Student
from .serializers import StudentSerializer
from department.models import Department
from django.db.models import Q
from studentCourse.models import StudentCourse

# Create your views here.
class StudentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class StudentListCreateView(generics.ListCreateAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentSerializer
    pagination_class = StudentPagination

    def get_queryset(self):
        user = self.request.user
        
        try:
            hod_dept = Department.objects.get(hod_id=user)
            queryset = Student.objects.filter(dept_id=hod_dept)
            
            # Handle search
            search_query = self.request.query_params.get('search', None)
            if search_query:
                queryset = queryset.filter(
                    Q(student_id__first_name__icontains=search_query) |
                    Q(student_id__last_name__icontains=search_query) |
                    Q(student_id__email__icontains=search_query) |
                    Q(roll_no__icontains=search_query)
                )
            
            # Handle year filter
            year_filter = self.request.query_params.get('year', None)
            if year_filter:
                queryset = queryset.filter(year=year_filter)
            
            # Handle semester filter
            semester_filter = self.request.query_params.get('current_semester', None)
            if semester_filter:
                queryset = queryset.filter(current_semester=semester_filter)
            
            # Handle student type filter
            student_type_filter = self.request.query_params.get('student_type', None)
            if student_type_filter:
                queryset = queryset.filter(student_type=student_type_filter)
            
            return queryset
        except Department.DoesNotExist:
            return Student.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        try:
            hod_dept = Department.objects.get(hod_id=user)
            
            if serializer.validated_data.get('dept_id') != hod_dept:
                raise serializers.ValidationError(
                    "You can only add students to your own department"
                )
                
            serializer.save()
        except Department.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Only HOD can create student records."}
            )

class StudentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StudentSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        
        try:
            hod_dept = Department.objects.get(hod_id=user)
            return Student.objects.filter(dept_id=hod_dept)
        except Department.DoesNotExist:
            return Student.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        try:
            hod_dept = Department.objects.get(hod_id=user)
            instance = self.get_object()
            
            if 'dept_id' in serializer.validated_data:
                if serializer.validated_data['dept_id'] != hod_dept:
                    raise serializers.ValidationError(
                        {"dept_id": "You can only manage students from your department"}
                    )
            
            serializer.save()
        except Department.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Only HOD can update student records."}
            )

class StudentStatsView(APIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = self.request.user
        
        try:
            hod_dept = Department.objects.get(hod_id=user)
            students = Student.objects.filter(dept_id=hod_dept)
            
            # Get counts by year
            year_stats = students.values('year').annotate(count=Count('id')).order_by('year')
            
            # Get counts by semester
            semester_stats = students.values('current_semester').annotate(count=Count('id')).order_by('current_semester')
            
            # Get counts by student type
            type_stats = students.values('student_type').annotate(count=Count('id'))
            
            # Get counts by degree type
            degree_stats = students.values('degree_type').annotate(count=Count('id'))
            
            # Get total count
            total_count = students.count()
            
            response_data = {
                'total': total_count,
                'by_year': year_stats,
                'by_semester': semester_stats,
                'by_student_type': type_stats,
                'by_degree_type': degree_stats
            }
            
            return Response(response_data)
        except Department.DoesNotExist:
            return Response(
                {"detail": "You need to be an HOD to access student statistics."},
                status=status.HTTP_403_FORBIDDEN
            )

class DepartmentStudentCountView(APIView):
    """
    API view to get student count for a specific department
    """
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, dept_id):
        try:
            # Get department
            try:
                department = Department.objects.get(id=dept_id)
            except Department.DoesNotExist:
                return Response(
                    {"detail": "Department not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get students for this department
            students = Student.objects.filter(dept_id=department)
            student_count = students.count()
            
            # Get batch year-wise breakdown
            batch_breakdown = students.values('batch').annotate(count=Count('id')).order_by('-batch')
            
            # Get year-wise breakdown
            year_breakdown = students.values('year').annotate(count=Count('id')).order_by('year')
            
            # Get semester-wise breakdown
            semester_breakdown = students.values('current_semester').annotate(count=Count('id')).order_by('current_semester')
            
            response_data = {
                'department_id': dept_id,
                'department_name': department.dept_name,
                'total_students': student_count,
                'batch_breakdown': batch_breakdown,
                'year_breakdown': year_breakdown,
                'semester_breakdown': semester_breakdown
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StudentProfileView(APIView):
    """API view to get the current student's profile information"""
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type != 'student':
            return Response(
                {"detail": "Only students can access their profile information."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            # Get the student profile for the current user
            student = Student.objects.filter(student_id=request.user).select_related('dept_id').first()
            
            if not student:
                return Response(
                    {"detail": "Student profile not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate total credits from all semesters
            total_credits = StudentCourse.objects.filter(
                student_id=student
            ).select_related('course_id').aggregate(
                total=Sum('course_id__credits')
            )['total'] or 0
                
            # Serialize with depth to include department details
            serializer = StudentSerializer(student, context={'request': request})
            
            # Combine student data with total credits
            data = serializer.data
            data['total_credits'] = total_credits
            
            return Response(data)
            
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )