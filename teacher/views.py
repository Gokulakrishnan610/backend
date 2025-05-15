from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from authentication.authentication import IsAuthenticated
from .models import Teacher, TeacherAvailability
from .serializers import (
    TeacherSerializer, CreateTeacherSerializer, UpdateTeacherSerializer,
    TeacherAvailabilitySerializer, CreateTeacherAvailabilitySerializer, 
    UpdateTeacherAvailabilitySerializer
)

class AddNewTeacher(generics.CreateAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateTeacherSerializer

    def post(self, request):
        try:
            is_hod = Teacher.objects.filter(
                teacher_id=request.user,
                teacher_role='HOD'
            ).exists()
            
            if not is_hod:
                return Response(
                    {
                        'detail': "Only HOD can add new teachers.",
                        "code": "permission_denied"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(
                {
                    'detail': "Teacher added successfully.",
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            print(e)
            return Response(
                {
                    'detail': "Something went wrong!",
                    "code": "internal_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreatePlaceholderTeacher(generics.CreateAPIView):
    """
    Create a placeholder teacher entry for future recruitment planning
    """
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateTeacherSerializer
    
    def post(self, request):
        try:
            # Check if user is HOD
            is_hod = Teacher.objects.filter(
                teacher_id=request.user,
                teacher_role='HOD'
            ).exists()
            
            if not is_hod:
                return Response(
                    {
                        'detail': "Only HOD can create placeholder teacher entries.",
                        "code": "permission_denied"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Set placeholder flag to true
            request.data['is_placeholder'] = True
            
            # Get HOD's department
            hod_dept = Teacher.objects.get(
                teacher_id=request.user,
                teacher_role='HOD'
            ).dept_id
            
            # If no department_id provided, use HOD's department
            if 'dept_id' not in request.data or not request.data['dept_id']:
                request.data['dept_id'] = hod_dept.id if hod_dept else None
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(
                {
                    'detail': "Placeholder teacher position created successfully.",
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            print(e)
            return Response(
                {
                    'detail': "Something went wrong!",
                    "code": "internal_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TeacherListView(generics.ListAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeacherSerializer

    def get_queryset(self):
        user = self.request.user
        
        try:
            hod_dept = Teacher.objects.get(
                teacher_id=user,
                teacher_role='HOD'
            ).dept_id
            return Teacher.objects.filter(dept_id=hod_dept)
        except Teacher.DoesNotExist:
            return Teacher.objects.filter(teacher_id=user)
            
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Filter industry professionals if requested
        is_industry = request.query_params.get('is_industry_professional')
        if is_industry:
            is_industry_bool = is_industry.lower() == 'true'
            queryset = queryset.filter(is_industry_professional=is_industry_bool)
            
        # Filter by teacher role if requested
        role = request.query_params.get('teacher_role')
        if role:
            queryset = queryset.filter(teacher_role=role)
            
        # Filter by resignation status if requested
        resignation_status = request.query_params.get('resignation_status')
        if resignation_status:
            queryset = queryset.filter(resignation_status=resignation_status)
            
        # Filter placeholder teachers if requested
        is_placeholder = request.query_params.get('is_placeholder')
        if is_placeholder:
            is_placeholder_bool = is_placeholder.lower() == 'true'
            queryset = queryset.filter(is_placeholder=is_placeholder_bool)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class TeacherDetailView(generics.RetrieveUpdateAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Teacher.objects.all()
    lookup_field = 'id'
    
    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return UpdateTeacherSerializer
        return TeacherSerializer

    def get_object(self):
        teacher_id = self.kwargs.get('id')
        teacher = get_object_or_404(Teacher, id=teacher_id)
        
        user = self.request.user
        is_hod = Teacher.objects.filter(
            teacher_id=user,
            teacher_role='HOD',
            dept_id=teacher.dept_id
        ).exists()
        
        if not is_hod and teacher.teacher_id != user:
            self.permission_denied(
                self.request,
                message="You don't have permission to access this teacher's details."
            )
        
        return teacher

    def patch(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_teacher = serializer.save()
            
            # After updating, use the regular serializer to return the complete data
            response_serializer = TeacherSerializer(updated_teacher)
            
            return Response(
                {
                    'detail': "Teacher updated successfully.",
                    'data': response_serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    'detail': "Something went wrong!",
                    "code": "internal_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class TeacherAvailabilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing teacher availability for industry professionals/POP
    """
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    queryset = TeacherAvailability.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTeacherAvailabilitySerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateTeacherAvailabilitySerializer
        return TeacherAvailabilitySerializer
    
    def get_queryset(self):
        """Only return availability slots for teachers the user has permission to view"""
        user = self.request.user
        
        # Check if user is an HOD
        try:
            hod_teacher = Teacher.objects.get(teacher_id=user, teacher_role='HOD')
            # HODs can see all availability slots for teachers in their department
            return TeacherAvailability.objects.filter(teacher__dept_id=hod_teacher.dept_id)
        except Teacher.DoesNotExist:
            # Regular teachers can only see their own availability slots
            try:
                teacher = Teacher.objects.get(teacher_id=user)
                return TeacherAvailability.objects.filter(teacher=teacher)
            except Teacher.DoesNotExist:
                return TeacherAvailability.objects.none()
    
    @action(detail=False, methods=['get'])
    def my_availability(self, request):
        """Get the current teacher's availability slots"""
        try:
            teacher = Teacher.objects.get(teacher_id=request.user)
            availability = TeacherAvailability.objects.filter(teacher=teacher)
            serializer = self.get_serializer(availability, many=True)
            return Response(serializer.data)
        except Teacher.DoesNotExist:
            return Response(
                {'detail': 'You are not registered as a teacher'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def teacher_availability(self, request, pk=None):
        """Get availability slots for a specific teacher"""
        teacher = get_object_or_404(Teacher, pk=pk)
        
        # Check permission
        user = request.user
        is_hod = Teacher.objects.filter(
            teacher_id=user,
            teacher_role='HOD',
            dept_id=teacher.dept_id
        ).exists()
        
        if not is_hod and teacher.teacher_id != user:
            return Response(
                {'detail': "You don't have permission to view this teacher's availability."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        availability = TeacherAvailability.objects.filter(teacher=teacher)
        serializer = self.get_serializer(availability, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create new availability slot"""
        # Check if the user is trying to create availability for themselves or if HOD
        teacher_id = request.data.get('teacher')
        
        if teacher_id:
            teacher = get_object_or_404(Teacher, pk=teacher_id)
            user = request.user
            
            is_hod = Teacher.objects.filter(
                teacher_id=user,
                teacher_role='HOD',
                dept_id=teacher.dept_id
            ).exists()
            
            if not is_hod and teacher.teacher_id != user:
                return Response(
                    {'detail': "You don't have permission to add availability for this teacher."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )