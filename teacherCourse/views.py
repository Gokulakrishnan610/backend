from django.shortcuts import render
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from authentication.authentication import IsAuthenticated
from .models import TeacherCourse
from .serializers import TeacherCourseSerializer
from department.models import Department
from django.core.exceptions import ValidationError
from teacher.models import Teacher

# Create your views here.
class TeacherCourseListView(generics.ListCreateAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeacherCourseSerializer

    def get_queryset(self):
        user = self.request.user
        
        # Admin users can see all assignments
        if user.is_superuser:
            return TeacherCourse.objects.all()
            
        try:
            teacher = Teacher.objects.get(teacher_id=user)
            
            # If user is HOD, return all department assignments
            if teacher.teacher_role == 'HOD' and teacher.dept_id:
                return TeacherCourse.objects.filter(
                    teacher_id__dept_id=teacher.dept_id,
                    course_id__teaching_dept_id=teacher.dept_id
                )
            # For regular teachers, only show their own assignments
            else:
                return TeacherCourse.objects.filter(teacher_id=teacher)
        except Teacher.DoesNotExist:
            return TeacherCourse.objects.none()

    def perform_create(self, serializer):
        user = self.request.user    
        response_warning = None
        # Admin users can create assignments for any department
        if user.is_superuser or user.is_staff:
            try:
                teacher_to_assign = serializer.validated_data['teacher_id']
                if teacher_to_assign.resignation_status == 'resigned':
                    raise serializers.ValidationError(
                        {"teacher_id": "Cannot assign a resigned teacher to courses."}
                    )
                instance = serializer.save()
                # Check for workload warning
                if hasattr(serializer, '_workload_exceeded') and serializer._workload_exceeded:
                    response_warning = f"Warning: Teacher workload limit exceeded. Assignment created, but total workload is above allowed hours."
                self._response_warning = response_warning
                return
            except ValidationError as e:
                raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        try:
            teacher = Teacher.objects.get(teacher_id=user)
            teacher_to_assign = serializer.validated_data['teacher_id']
            course = serializer.validated_data['course_id']
            if teacher_to_assign.resignation_status == 'resigned':
                raise serializers.ValidationError(
                    {"teacher_id": "Cannot assign a resigned teacher to courses."}
                )
            if teacher.teacher_role != 'HOD':
                raise serializers.ValidationError(
                    {"detail": "Only HOD or admin can create teacher course assignments."}
                )
            if teacher_to_assign.dept_id != teacher.dept_id or course.teaching_dept_id != teacher.dept_id:
                raise serializers.ValidationError(
                    {"detail": "You can only assign teachers and courses from your own department"}
                )
            try:
                instance = serializer.save()
                if hasattr(serializer, '_workload_exceeded') and serializer._workload_exceeded:
                    response_warning = f"Warning: Teacher workload limit exceeded. Assignment created, but total workload is above allowed hours."
                self._response_warning = response_warning
            except ValidationError as e:
                raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
        except Teacher.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Teacher profile not found. Cannot create assignments."}
            )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        warning = getattr(self, '_response_warning', None)
        if warning:
            response.data['warning'] = warning
        return response

class TeacherCourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TeacherCourseSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        
        # Admin users can see all assignments
        if user.is_superuser or user.is_staff:
            return TeacherCourse.objects.all()
        
        try:
            teacher = Teacher.objects.get(teacher_id=user)
            
            # If user is HOD, return all department assignments
            if teacher.teacher_role == 'HOD' and teacher.dept_id:
                return TeacherCourse.objects.filter(
                    teacher_id__dept_id=teacher.dept_id,
                    course_id__teaching_dept_id=teacher.dept_id
                )
            # For regular teachers, only show their own assignments
            else:
                return TeacherCourse.objects.filter(teacher_id=teacher)
        except Teacher.DoesNotExist:
            return TeacherCourse.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        
        # Admin users can update any assignment
        if user.is_superuser or user.is_staff:
            # Check if updating with a resigned teacher
            if 'teacher_id' in serializer.validated_data:
                teacher_to_assign = serializer.validated_data['teacher_id']
                if teacher_to_assign.resignation_status == 'resigned':
                    raise serializers.ValidationError(
                        {"teacher_id": "Cannot assign a resigned teacher to courses."}
                    )
            
            serializer.save()
            return
            
        try:
            teacher = Teacher.objects.get(teacher_id=user)
            
            # Only HOD can update assignments
            if teacher.teacher_role != 'HOD':
                raise serializers.ValidationError(
                    {"detail": "Only HOD or admin can update teacher course assignments."}
                )
            
            instance = self.get_object()
            
            if 'teacher_id' in serializer.validated_data:
                teacher_to_assign = serializer.validated_data['teacher_id']
                
                # Check if teacher has resigned
                if teacher_to_assign.resignation_status == 'resigned':
                    raise serializers.ValidationError(
                        {"teacher_id": "Cannot assign a resigned teacher to courses."}
                    )
                
                if teacher_to_assign.dept_id != teacher.dept_id:
                    raise serializers.ValidationError(
                        {"teacher_id": "You can only assign teachers from your department."}
                    )
            
            if 'course_id' in serializer.validated_data:
                if serializer.validated_data['course_id'].teaching_dept_id != teacher.dept_id:
                    raise serializers.ValidationError(
                        {"course_id": "You can only assign courses from your department."}
                    )
            
            serializer.save()
        except Teacher.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Teacher profile not found. Cannot update assignments."}
            )
            
    def perform_destroy(self, instance):
        user = self.request.user
        
        # Admin users can delete any assignment
        if user.is_superuser or user.is_staff:
            instance.delete()
            return
            
        try:
            teacher = Teacher.objects.get(teacher_id=user)
            
            # Only HOD can delete assignments
            if teacher.teacher_role != 'HOD':
                raise serializers.ValidationError(
                    {"detail": "Only HOD or admin can delete teacher course assignments."}
                )
                
            instance.delete()
        except Teacher.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Teacher profile not found. Cannot delete assignments."}
            )

class TeacherAssignmentsByTeacherView(APIView):
    """
    API view to get all course assignments for a specific teacher
    """
    authentication_classes = [IsAuthenticated]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, teacher_id):
        try:
            # Check permissions
            user = request.user
            
            # Admin users can see any teacher's assignments
            if not (user.is_superuser or user.is_staff):
                try:
                    # Check if the user is requesting their own data or is an HOD
                    user_teacher = Teacher.objects.get(teacher_id=user)
                    
                    # If user is not HOD and not requesting their own data, deny
                    if user_teacher.teacher_role != 'HOD' and user_teacher.id != teacher_id:
                        return Response(
                            {"detail": "You don't have permission to view other teachers' assignments."},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    
                    # If user is HOD but teacher is not in their department, deny
                    if user_teacher.teacher_role == 'HOD' and user_teacher.dept_id:
                        requested_teacher = Teacher.objects.get(id=teacher_id)
                        if requested_teacher.dept_id != user_teacher.dept_id:
                            return Response(
                                {"detail": "You can only view assignments for teachers in your department."},
                                status=status.HTTP_403_FORBIDDEN
                            )
                except Teacher.DoesNotExist:
                    return Response(
                        {"detail": "Teacher profile not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Get assignments for the specified teacher
            teacher = Teacher.objects.get(id=teacher_id)
            assignments = TeacherCourse.objects.filter(teacher_id=teacher)
            serializer = TeacherCourseSerializer(assignments, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Teacher.DoesNotExist:
            return Response(
                {"detail": "Teacher not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )