from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from authentication.authentication import IsAuthenticated
from .models import Course, CourseResourceAllocation, CourseRoomPreference
from teacherCourse.models import TeacherCourse
from department.models import Department
from django.db import models
from rest_framework.views import APIView
from django.core.exceptions import PermissionDenied
from .serializers import CourseSerializer, CreateCourseSerializer, UpdateCourseSerializer, CourseResourceAllocationSerializer, CourseRoomPreferenceSerializer
from rest_framework import serializers
from teacher.models import Teacher
from course.models import Course

class AddNewCourse(generics.CreateAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateCourseSerializer

    def post(self, request):
        try:
            is_hod = Department.objects.filter(hod_id=request.user).exists()
            
            if not is_hod:
                return Response(
                    {
                        'detail': "Only HOD can add new courses.",
                        "code": "permission_denied"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            course = serializer.save()
            
            response_serializer = CourseSerializer(course, context={'request': request})
            
            return Response(
                {
                    'detail': "Course added successfully.",
                    'data': response_serializer.data
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

class CourseListView(generics.ListCreateAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateCourseSerializer
        return CourseSerializer

    def get_queryset(self):
        user = self.request.user
        try:
            hod_dept = Department.objects.get(hod_id=user)
            return Course.objects.filter(teaching_dept_id=hod_dept)
        except Department.DoesNotExist:
            return Course.objects.none()
    
    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        return context

    def post(self, request, *args, **kwargs):
        try:
            is_hod = Department.objects.filter(hod_id=request.user).exists()
            
            if not is_hod:
                return Response(
                    {
                        'detail': "Only HOD can add new courses.",
                        "code": "permission_denied"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            course = serializer.save()
            
            response_serializer = CourseSerializer(course, context={'request': request})
            
            return Response(
                {
                    'detail': "Course added successfully.",
                    'data': response_serializer.data
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

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseSerializer
    lookup_field = 'id'
    
    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return UpdateCourseSerializer
        return CourseSerializer

    def get_object(self):
        course_id = self.kwargs.get('id')
        # Use select_related to fetch related departments and course master in a single query
        # This automatically loads:
        # - course_id (CourseMaster)
        # - course_id__course_dept_id (Department)  
        # - for_dept_id (Department)
        # - teaching_dept_id (Department)
        course = get_object_or_404(
            Course.objects.select_related(
                'course_id', 
                'course_id__course_dept_id',
                'for_dept_id', 
                'teaching_dept_id'
            ), 
            id=course_id
        )
        
        # Check if user has permission to edit/delete this course
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            user = self.request.user
            
            # Get user's department (if HOD)
            user_dept = None
            try:
                user_dept = Department.objects.get(hod_id=user)
            except Department.DoesNotExist:
                pass
            
            if user_dept:
                # Owner department - full rights (edit and delete)
                is_owner = user_dept.id == course.course_id.course_dept_id.id
                
                # Teaching department - has edit and delete rights
                is_teacher = user_dept.id == course.teaching_dept_id.id if course.teaching_dept_id else False
                
                # For department - only has delete rights, no edit rights
                is_learner = user_dept.id == course.for_dept_id.id if course.for_dept_id else False
                
                # If DELETE, allow owner, teaching, or for department to delete
                if self.request.method == 'DELETE' and not (is_owner or is_teacher or is_learner):
                    self.permission_denied(
                        self.request,
                        message="Only the owner, teaching, or for department's HOD can delete this course."
                    )
                
                # If EDIT (PUT/PATCH), only owner or teacher can edit
                if self.request.method in ['PUT', 'PATCH']:
                    if not (is_owner or is_teacher):
                        self.permission_denied(
                            self.request,
                            message="Only the owner or teaching department's HOD can edit this course."
                        )
                    
                    # Restrict changing of department assignments regardless of role
                    if 'for_dept_id' in self.request.data or 'teaching_dept_id' in self.request.data:
                        self.permission_denied(
                            self.request,
                            message="Department assignments cannot be changed through this interface. Use course reassignment instead."
                        )
            else:
                # Not an HOD of any department
                self.permission_denied(
                    self.request,
                    message="You don't have permission to modify this course."
                )
    
        return course
        
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            # Get relationship type for the user's perspective
            user_dept = None
            try:
                user_dept = Department.objects.get(hod_id=request.user)
            except Department.DoesNotExist:
                pass
            
            response_data = serializer.data
            if user_dept:
                # Add user's relationship to this course
                owning_dept_id = instance.course_id.course_dept_id.id if instance.course_id and instance.course_id.course_dept_id else None
                for_dept_id = instance.for_dept_id.id if instance.for_dept_id else None
                teaching_dept_id = instance.teaching_dept_id.id if instance.teaching_dept_id else None
                
                user_roles = []
                if user_dept.id == owning_dept_id:
                    user_roles.append("owner")
                if user_dept.id == for_dept_id:
                    user_roles.append("learner")
                if user_dept.id == teaching_dept_id:
                    user_roles.append("teacher")
                
                response_data['user_department_roles'] = user_roles
            
            return Response(
                {
                    'status': 'success',
                    'data': response_data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    'status': 'error',
                    'detail': "Something went wrong!",
                    "code": "internal_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user_dept = None
            try:
                user_dept = Department.objects.get(hod_id=request.user)
            except Department.DoesNotExist:
                pass
            
            # Get editable fields from the serializer for the current user's department
            if user_dept:
                # Owner department - full rights
                is_owner = user_dept.id == instance.course_id.course_dept_id.id
                # Teaching department
                is_teacher = user_dept.id == instance.teaching_dept_id.id if instance.teaching_dept_id else False
                
                # Get appropriate editable fields based on department role
                allowed_fields = []
                if is_owner:
                    allowed_fields = [
                        'course_year', 'course_semester',
                        'need_assist_teacher',
                        'elective_type', 'lab_type', 'teaching_status', 'no_of_students'
                    ]
                elif is_teacher:
                    # Teaching department can edit more than just teaching_status
                    allowed_fields = ['teaching_status', 'no_of_students', 'course_year', 'course_semester', 'need_assist_teacher']
                
                # Only keep allowed fields
                if not is_owner:  # Owner can edit all fields
                    for field in list(request.data.keys()):
                        if field not in allowed_fields:
                            request.data.pop(field, None)
            
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_course = serializer.save()
            
            response_serializer = CourseSerializer(updated_course)
            
            return Response(
                {
                    'detail': "Course updated successfully.",
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

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {
                    'detail': "Course deleted successfully."
                },
                status=status.HTTP_204_NO_CONTENT
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

class CourseResourceAllocationListCreateView(generics.ListCreateAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseResourceAllocationSerializer

    def get_queryset(self):
        user = self.request.user
        try:
            user_dept = Department.objects.get(hod_id=user)
            # Return allocations where the user's department is either the original or the teaching department
            return CourseResourceAllocation.objects.filter(
                models.Q(original_dept_id=user_dept) | 
                models.Q(teaching_dept_id=user_dept)
            ).select_related('course_id', 'original_dept_id', 'teaching_dept_id')
        except Department.DoesNotExist:
            return CourseResourceAllocation.objects.none()
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get the user's department
        user_dept = None
        try:
            user_dept = Department.objects.get(hod_id=request.user)
        except Department.DoesNotExist:
            return Response(
                {
                    'status': 'error',
                    'detail': 'User is not a HOD of any department'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Separate incoming and outgoing allocations
        incoming_allocations = queryset.filter(
            teaching_dept_id=user_dept
        ).exclude(
            original_dept_id=user_dept
        )
        
        outgoing_allocations = queryset.filter(
            original_dept_id=user_dept
        )
        
        # Serialize both sets of allocations
        incoming_serializer = self.get_serializer(incoming_allocations, many=True)
        outgoing_serializer = self.get_serializer(outgoing_allocations, many=True)
        
        return Response(
            {
                'status': 'success',
                'user_department_id': user_dept.id,
                'user_department_name': user_dept.dept_name,
                'incoming_allocations': incoming_serializer.data,
                'outgoing_allocations': outgoing_serializer.data
            },
            status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        try:
            # Check if user is an HOD
            user_dept = None
            try:
                user_dept = Department.objects.get(hod_id=request.user)
            except Department.DoesNotExist:
                return Response(
                    {
                        'detail': "Only department HODs can request resource allocation.",
                        "code": "permission_denied"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get the course
            course_id = request.data.get('course_id')
            try:
                course = Course.objects.select_related('course_id', 'course_id__course_dept_id', 'teaching_dept_id', 'for_dept_id').get(id=course_id)
            except Course.DoesNotExist:
                return Response(
                    {
                        'detail': "Course not found.",
                        "code": "not_found"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verify the requester is either from the course's owning department or the current teaching department
            is_owner = course.course_id.course_dept_id and course.course_id.course_dept_id.id == user_dept.id
            is_teaching = course.teaching_dept_id and course.teaching_dept_id.id == user_dept.id
            
            if not (is_owner or is_teaching):
                return Response(
                    {
                        'detail': "Only the course owner department or current teaching department can request allocation.",
                        "code": "permission_denied"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # Check if there's already a pending or approved allocation for this course with the same teaching department
            teaching_dept_id = request.data.get('teaching_dept_id')
            existing_allocation = CourseResourceAllocation.objects.filter(
                course_id=course_id,
                teaching_dept_id=teaching_dept_id,
                status__in=['pending', 'approved']
            ).exists()
            
            if existing_allocation:
                return Response(
                    {
                        'detail': "A resource allocation request already exists for this course with the selected teaching department.",
                        "code": "duplicate_request"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Check if the course is already taught by the requested department
            if course.teaching_dept_id and course.teaching_dept_id.id == int(teaching_dept_id):
                return Response(
                    {
                        'detail': "This department is already teaching this course.",
                        "code": "already_teaching"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the allocation request
            data = {
                'course_id': course_id,
                'original_dept_id': user_dept.id,
                'teaching_dept_id': teaching_dept_id,
                'allocation_reason': request.data.get('allocation_reason', ''),
                'status': 'pending'
            }
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            allocation = serializer.save()
            
            return Response(
                {
                    'detail': "Resource allocation request created successfully.",
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

class CourseResourceAllocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseResourceAllocationSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        return CourseResourceAllocation.objects.all()
    
    def get_object(self):
        allocation_id = self.kwargs.get('id')
        allocation = get_object_or_404(
            CourseResourceAllocation.objects.select_related(
                'course_id', 
                'original_dept_id', 
                'teaching_dept_id'
            ), 
            id=allocation_id
        )
        
        # Check permissions
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            user = self.request.user
            user_dept = None
            try:
                user_dept = Department.objects.get(hod_id=user)
            except Department.DoesNotExist:
                self.permission_denied(
                    self.request,
                    message="You don't have permission to modify this allocation."
                )
            
            if user_dept:
                # Original dept can update or delete the request while it's pending
                is_original_dept = user_dept.id == allocation.original_dept_id.id
                
                # Teaching dept can only respond to the request (approve/reject)
                is_teaching_dept = user_dept.id == allocation.teaching_dept_id.id
                
                # If DELETE, only original dept can delete pending requests
                if self.request.method == 'DELETE':
                    if not is_original_dept or allocation.status != 'pending':
                        self.permission_denied(
                            self.request,
                            message="Only the original department's HOD can delete pending allocation requests."
                        )
                
                # For PATCH, check who's making the request
                if self.request.method == 'PATCH':
                    # Original dept can update anything while pending
                    if is_original_dept and allocation.status != 'pending':
                        self.permission_denied(
                            self.request,
                            message="Original department can only modify pending requests."
                        )
                    
                    # Teaching dept can only update status
                    if is_teaching_dept:
                        # Check that we're only updating status
                        if set(self.request.data.keys()) - {'status'}:
                            self.permission_denied(
                                self.request,
                                message="Teaching department can only update the status field."
                            )
                    
                    # Neither original nor teaching dept
                    if not (is_original_dept or is_teaching_dept):
                        self.permission_denied(
                            self.request,
                            message="You don't have permission to update this allocation."
                        )
            else:
                self.permission_denied(
                    self.request,
                    message="You don't have permission to modify this allocation."
                )
        
        return allocation
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(
                {
                    'status': 'success',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    'status': 'error',
                    'detail': "Something went wrong!",
                    'code': 'internal_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, *args, **kwargs):
        try:
            allocation = self.get_object()
            
            # Get user department
            user_dept = Department.objects.get(hod_id=request.user)
            
            # If teaching department is updating status
            if user_dept.id == allocation.teaching_dept_id.id and 'status' in request.data:
                status_value = request.data.get('status')
                
                # If approving the request, also update the course's teaching_dept_id
                if status_value == 'approved':
                    course = allocation.course_id
                    course.teaching_dept_id = allocation.teaching_dept_id
                    course.save()
            
            # Update the allocation
            serializer = self.get_serializer(allocation, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_allocation = serializer.save()
            
            return Response(
                {
                    'status': 'success',
                    'detail': "Resource allocation updated successfully.",
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    'status': 'error',
                    'detail': "Something went wrong!",
                    'code': 'internal_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {
                    'status': 'success',
                    'detail': 'Resource allocation request deleted successfully.'
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    'status': 'error',
                    'detail': "Something went wrong!",
                    'code': 'internal_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CourseRoomPreferenceListCreateView(generics.ListCreateAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseRoomPreferenceSerializer

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return CourseRoomPreference.objects.filter(course_id=course_id)
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(
                {
                    'detail': "Something went wrong!",
                    "code": "internal_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # Check permissions before saving (will raise PermissionDenied if not allowed)
        self.check_course_permission(course)
        
        # If we reach here, permission is granted
        serializer.save(course_id=course)
    
    def check_course_permission(self, course):
        """
        Check if the current user has permission to modify room preferences for the course.
        Returns True if permission is granted, False otherwise.
        """
        try:
            # Find user's department (using Department model for HOD)
            user_dept = None
            
            # Check if user is HOD of any department
            try:
                hod_dept = Department.objects.get(hod_id=self.request.user)
                user_dept = hod_dept
            except Department.DoesNotExist:
                # Check if user is a teacher
                if hasattr(self.request.user, 'teacher_profile') and hasattr(self.request.user.teacher_profile, 'dept_id'):
                    user_dept = self.request.user.teacher_profile.dept_id
            
            if not user_dept:
                raise PermissionDenied("Unable to determine your department. You must be a HOD or teacher with department association.")
            
            # Check permissions based on department
            is_owner = False
            is_teacher = False
            
            if course.course_id and course.course_id.course_dept_id:
                is_owner = user_dept.id == course.course_id.course_dept_id.id
                
            if course.teaching_dept_id:
                is_teacher = user_dept.id == course.teaching_dept_id.id
            
            is_for_dept = course.for_dept_id and user_dept.id == course.for_dept_id.id
            
            if is_owner or is_teacher:
                return True
            elif is_for_dept:
                raise PermissionDenied("For departments cannot modify room preferences. Only course owner or teaching department can make changes.")
            else:
                raise PermissionDenied("You don't have permission to modify room preferences for this course.")
            
        except PermissionDenied:
            # Re-raise permission denied exceptions
            raise
        except Exception as e:
            print(f"Permission check error: {e}")
            raise PermissionDenied("Unable to determine permissions for this action.")
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response(
                {
                    'detail': "Room preference added successfully.",
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except PermissionDenied as pd:
            return Response(
                {
                    'detail': str(pd),
                    'code': 'permission_denied'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        except serializers.ValidationError as ve:
            # Extract error message properly
            if hasattr(ve, 'detail'):
                if isinstance(ve.detail, dict) and 'detail' in ve.detail:
                    # Case when we raised our custom format
                    return Response(
                        {
                            'detail': ve.detail['detail'],
                            'code': ve.detail.get('code', 'validation_error')
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # Standard validation error
                    return Response(
                        {
                            'detail': str(ve.detail),
                            'code': 'validation_error'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {
                        'detail': str(ve),
                        'code': 'validation_error'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            print(e)
            return Response(
                {
                    'detail': str(e) if hasattr(e, '__str__') else "Something went wrong!",
                    'code': "internal_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CourseRoomPreferenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseRoomPreferenceSerializer
    
    def get_object(self):
        preference_id = self.kwargs.get('id')
        course_id = self.kwargs.get('course_id')
        preference = get_object_or_404(
            CourseRoomPreference,
            id=preference_id,
            course_id=course_id
        )
        
        # Check if user's department is the course owner or teaching department
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            self.check_course_permission(preference.course_id)
        
        return preference
    
    def check_course_permission(self, course):
        """
        Check if the current user has permission to modify room preferences for the course.
        Returns True if permission is granted, False otherwise.
        """
        try:
            # Find user's department (using Department model for HOD)
            user_dept = None
            
            # Check if user is HOD of any department
            try:
                hod_dept = Department.objects.get(hod_id=self.request.user)
                user_dept = hod_dept
            except Department.DoesNotExist:
                # Check if user is a teacher
                if hasattr(self.request.user, 'teacher_profile') and hasattr(self.request.user.teacher_profile, 'dept_id'):
                    user_dept = self.request.user.teacher_profile.dept_id
            
            if not user_dept:
                raise PermissionDenied("Unable to determine your department. You must be a HOD or teacher with department association.")
            
            # Check permissions based on department
            is_owner = False
            is_teacher = False
            
            if course.course_id and course.course_id.course_dept_id:
                is_owner = user_dept.id == course.course_id.course_dept_id.id
                
            if course.teaching_dept_id:
                is_teacher = user_dept.id == course.teaching_dept_id.id
            
            is_for_dept = course.for_dept_id and user_dept.id == course.for_dept_id.id
            
            if is_owner or is_teacher:
                return True
            elif is_for_dept:
                raise PermissionDenied("For departments cannot modify room preferences. Only course owner or teaching department can make changes.")
            else:
                raise PermissionDenied("You don't have permission to modify room preferences for this course.")
            
        except PermissionDenied:
            # Re-raise permission denied exceptions
            raise
        except Exception as e:
            print(f"Permission check error: {e}")
            raise PermissionDenied("Unable to determine permissions for this action.")
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PermissionDenied as pd:
            return Response(
                {
                    'detail': str(pd),
                    'code': 'permission_denied'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    'detail': "Something went wrong!",
                    'code': "internal_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(
                {
                    'detail': "Room preference updated successfully.",
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        except PermissionDenied as pd:
            return Response(
                {
                    'detail': str(pd),
                    'code': 'permission_denied'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        except serializers.ValidationError as ve:
            # Extract error message properly
            if hasattr(ve, 'detail'):
                if isinstance(ve.detail, dict) and 'detail' in ve.detail:
                    # Case when we raised our custom format
                    return Response(
                        {
                            'detail': ve.detail['detail'],
                            'code': ve.detail.get('code', 'validation_error')
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # Standard validation error
                    return Response(
                        {
                            'detail': str(ve.detail),
                            'code': 'validation_error'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {
                        'detail': str(ve),
                        'code': 'validation_error'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            print(e)
            return Response(
                {
                    'detail': str(e) if hasattr(e, '__str__') else "Something went wrong!",
                    'code': "internal_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return Response(
                {
                    'detail': "Room preference deleted successfully."
                },
                status=status.HTTP_204_NO_CONTENT
            )
        except PermissionDenied as pd:
            return Response(
                {
                    'detail': str(pd),
                    'code': 'permission_denied'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    'detail': "Something went wrong!",
                    'code': "internal_error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CourseAssignmentStatsView(APIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id=None):
        try:
            if course_id:
                # Get stats for a specific course
                course = Course.objects.get(id=course_id)
                assignments = TeacherCourse.objects.filter(course_id=course)
                stats = {
                    'course_id': course.id,
                    'course_name': course.course_id.course_name,
                    'course_code': course.course_id.course_id,
                    'total_teachers': assignments.count(),
                    'teachers': []
                }
                
                # Safely create teacher list with null checks
                for assignment in assignments:
                    teacher_name = "Unknown Teacher"
                    # Safely get teacher name with null checks
                    if assignment.teacher_id and assignment.teacher_id.teacher_id:
                        first_name = assignment.teacher_id.teacher_id.first_name or ''
                        last_name = assignment.teacher_id.teacher_id.last_name or ''
                        teacher_name = f"{first_name} {last_name}".strip()
                        if not teacher_name:
                            teacher_name = "Unnamed Teacher"
                    
                    stats['teachers'].append({
                        'assignment_id': assignment.id,
                        'teacher_id': assignment.teacher_id.id if assignment.teacher_id else None,
                        'teacher_name': teacher_name,
                        'semester': assignment.semester,
                        'academic_year': assignment.academic_year,
                        'student_count': assignment.student_count,
                        'is_assistant': assignment.is_assistant
                    })
            else:
                # Get stats for all courses
                courses = Course.objects.all()
                stats = []
                for course in courses:
                    assignments = TeacherCourse.objects.filter(course_id=course)
                    course_stats = {
                        'course_id': course.id,
                        'course_name': course.course_id.course_name,
                        'course_code': course.course_id.course_id,
                        'total_teachers': assignments.count(),
                        'teachers': []
                    }
                    
                    # Safely create teacher list with null checks
                    for assignment in assignments:
                        teacher_name = "Unknown Teacher"
                        # Safely get teacher name with null checks
                        if assignment.teacher_id and assignment.teacher_id.teacher_id:
                            first_name = assignment.teacher_id.teacher_id.first_name or ''
                            last_name = assignment.teacher_id.teacher_id.last_name or ''
                            teacher_name = f"{first_name} {last_name}".strip()
                            if not teacher_name:
                                teacher_name = "Unnamed Teacher"
                        
                        course_stats['teachers'].append({
                            'assignment_id': assignment.id,
                            'teacher_id': assignment.teacher_id.id if assignment.teacher_id else None,
                            'teacher_name': teacher_name,
                            'semester': assignment.semester,
                            'academic_year': assignment.academic_year,
                            'student_count': assignment.student_count,
                            'is_assistant': assignment.is_assistant
                        })
                    
                    stats.append(course_stats)
            
            return Response(stats)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=404)
        except Exception as e:
            import traceback
            print(f"Error in CourseAssignmentStatsView: {str(e)}")
            print(traceback.format_exc())
            return Response({'error': str(e)}, status=500)

        
class CourseNotification(APIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, req):
        try:
            teacher = Teacher.objects.get(teacher_id=req.user)
            teacher_dept = teacher.dept_id
            
            # Get all courses where the department is involved (as owner, teacher, or for_dept)
            dept_involved_courses = Course.objects.filter(
                models.Q(course_id__course_dept_id=teacher_dept) |  # Department owns the course
                models.Q(teaching_dept_id=teacher_dept) |           # Department teaches the course
                models.Q(for_dept_id=teacher_dept)                  # Course is for department's students
            ).select_related(
                'course_id',
                'course_id__course_dept_id',
                'teaching_dept_id',
                'for_dept_id'
            ).distinct()
            
            # Filter to find cross-department relationships only
            # These are courses where at least one of the departments is not the teacher's department
            cross_dept_courses = []
            for course in dept_involved_courses:
                owner_dept = course.course_id.course_dept_id
                teacher_dept_id = course.teaching_dept_id
                for_dept_id = course.for_dept_id
                
                # Skip courses where all departments are the same (fully internal)
                if owner_dept == teacher_dept_id == for_dept_id == teacher_dept:
                    continue
                
                # Add relationship details to help interpret course relationships
                course.relationship_details = {
                    "is_owner": owner_dept == teacher_dept,
                    "is_teacher": teacher_dept_id == teacher_dept,
                    "is_for_dept": for_dept_id == teacher_dept,
                    "departments_involved": {
                        "owner": owner_dept.dept_name,
                        "teacher": teacher_dept_id.dept_name if teacher_dept_id else "None",
                        "for_dept": for_dept_id.dept_name if for_dept_id else "None"
                    }
                }
                
                cross_dept_courses.append(course)
            
            serializer = CourseSerializer(cross_dept_courses, many=True)
            
            return Response({
                "detail": "Success",
                "data": serializer.data
            })
            
        except Teacher.DoesNotExist:
            return Response(
                {
                    "detail": "No data found",
                    "error": "no_data_found"
                },
                status=404
            )