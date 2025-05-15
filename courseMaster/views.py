from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import CourseMaster
from .serializers import CourseMasterSerializer
from rest_framework.permissions import IsAuthenticated
from authentication.authentication import JWTCookieAuthentication
from department.views import get_user_department
from utlis.pagination import PagePagination
from django.db.models import Q, Count

# Create your views here.
class CourseMasterListAPIView(generics.ListCreateAPIView):
    authentication_classes=[JWTCookieAuthentication]
    permission_classes=[IsAuthenticated]
    queryset = CourseMaster.objects.all()
    serializer_class = CourseMasterSerializer
    pagination_class = PagePagination
    
    def get_queryset(self):
        queryset = CourseMaster.objects.all()
        
        # Handle search
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(course_id__icontains=search_query) |
                Q(course_name__icontains=search_query)
            )
        
        # Allow filtering by department
        department_id = self.request.query_params.get('department_id', None)
        if department_id is not None:
            queryset = queryset.filter(course_dept_id=department_id)
            
        # Allow filtering by course type
        course_type = self.request.query_params.get('course_type', None)
        if course_type is not None:
            queryset = queryset.filter(course_type=course_type)
            
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        department_id, is_hod = get_user_department(request.user)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            
            # Add permissions to each course master
            for item in serializer.data:
                course_dept_id = item['course_dept_id']
                item['permissions'] = {
                    'can_edit': request.user.is_superuser or (department_id and course_dept_id == department_id),
                    'can_delete': request.user.is_superuser or (department_id and course_dept_id == department_id),
                    'is_owner': department_id and course_dept_id == department_id
                }
                
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        # If course_dept_id is not provided, use the user's department
        if 'course_dept_id' not in data or not data['course_dept_id']:
            department_id, _ = get_user_department(request.user)
            
            if not department_id:
                return Response({
                    "status": "error",
                    "detail": "User has no associated department. Please provide a course_dept_id."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            data['course_dept_id'] = department_id

        course_id = data.get('course_id')
        if course_id:
            if self.get_queryset().filter(course_id=course_id).exists():
                return Response({
                    "status": "error",
                    "detail": f"Course with course_id '{course_id}' already exists."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set default values for new fields if not provided
        if 'is_zero_credit_course' not in data:
            data['is_zero_credit_course'] = False
        if 'lecture_hours' not in data:
            data['lecture_hours'] = 0
        if 'practical_hours' not in data:
            data['practical_hours'] = 0
        if 'tutorial_hours' not in data:
            data['tutorial_hours'] = 0
        if 'credits' not in data:
            data['credits'] = 0
        if 'regulation' not in data:
            data['regulation'] = "0"
        if 'course_type' not in data:
            data['course_type'] = "T"  # Default to Theory
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({
                "status": "success",
                "message": "Course master created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED, headers=headers)
        return Response({
            "status": "error",
            "detail": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CourseMasterStatsAPIView(APIView):
    """
    API View to get statistics about course masters
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Get total courses count
        total_courses = CourseMaster.objects.count()
        
        # Get course types count
        theory_courses_count = CourseMaster.objects.filter(course_type='T').count()
        lab_courses_count = CourseMaster.objects.filter(course_type='L').count()
        combined_courses_count = CourseMaster.objects.filter(course_type='LoT').count()
        
        # Get zero credit courses count
        zero_credit_courses_count = CourseMaster.objects.filter(is_zero_credit_course=True).count()
        
        # Get departments stats
        department_stats = CourseMaster.objects.values(
            'course_dept_id', 
            'course_dept_id__dept_name'
        ).annotate(
            course_count=Count('id')
        ).order_by('-course_count')[:10]  # Top 10 departments
        
        # Process department stats to match expected format
        departments_data = [
            {
                'department_id': item['course_dept_id'],
                'department_name': item['course_dept_id__dept_name'],
                'course_count': item['course_count']
            }
            for item in department_stats
        ]
        
        # Get regulation stats
        regulation_stats = CourseMaster.objects.values(
            'regulation'
        ).annotate(
            course_count=Count('id')
        ).order_by('-course_count')
        
        # Process regulation stats to match expected format
        regulations_data = [
            {
                'regulation': item['regulation'],
                'course_count': item['course_count']
            }
            for item in regulation_stats
        ]
        
        # Combine all stats into one response
        response_data = {
            'total_courses': total_courses,
            'theory_courses_count': theory_courses_count,
            'lab_courses_count': lab_courses_count,
            'combined_courses_count': combined_courses_count,
            'zero_credit_courses_count': zero_credit_courses_count,
            'department_stats': departments_data,
            'regulation_stats': regulations_data
        }
        
        return Response(response_data)

class CourseMasterDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CourseMasterSerializer
    queryset = CourseMaster.objects.all()
    lookup_field = 'pk'
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        return get_object_or_404(CourseMaster, pk=pk)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Add permissions to the response
        department_id, is_hod = get_user_department(request.user)
        data = serializer.data
        
        # Add permissions information
        data['permissions'] = {
            'can_edit': request.user.is_superuser or (department_id and instance.course_dept_id.id == department_id),
            'can_delete': request.user.is_superuser or (department_id and instance.course_dept_id.id == department_id),
            'is_owner': department_id and instance.course_dept_id.id == department_id
        }
        
        return Response({
            "status": "success",
            "data": data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check permissions - allow updates if user is from the department that owns the course
        department_id, is_hod = get_user_department(request.user)
        if not department_id or (instance.course_dept_id.id != department_id and not request.user.is_superuser):
            return Response({
                "status": "error",
                "detail": "You do not have permission to update this course master."
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "status": "success",
                "message": "Course master updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "detail": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Update permissions - allow deletion if user is from the department that owns the course
        department_id, is_hod = get_user_department(request.user)
        if not department_id or (instance.course_dept_id.id != department_id and not request.user.is_superuser):
            return Response({
                "status": "error",
                "detail": "You do not have permission to delete this course master."
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            self.perform_destroy(instance)
            return Response({
                "status": "success",
                "message": "Course master deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                "status": "error",
                "detail": "Cannot delete course master as it may be in use.",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)