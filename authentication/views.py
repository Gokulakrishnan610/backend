from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import serializers
from .models import *
from .serializers import *
from .authentication import IsAuthenticated
from student.models import Student
from teacher.models import Teacher
from department.models import Department
import random

class DepartmentSerializerForProfile(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'dept_name', 'date_established', 'contact_info']

# Create your views here.
class CreateNewUserAPIView(generics.CreateAPIView):
    """
    API View to create a new user.
    Only accessible to authenticated users (e.g., admin or staff).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to create a new user.
        Sets a default password if none is provided.
        """
        # Add a default password to the request data if not provided
        request_data = request.data.copy()  # Make a mutable copy of request data
        if 'password' not in request_data:
            request_data['password'] = 'Changeme@123'  # Default password

        serializer = self.get_serializer(data=request_data)
        if serializer.is_valid():
            # Save the validated data to create a new user
            user = serializer.save()

            # Optionally, you can send a verification email here
            # user.send_verification_mail()

            return Response({
                "status": "success",
                "detail": "User created successfully.",
                "data": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number,
                    "gender": user.gender,
                }
            }, status=status.HTTP_201_CREATED)

        # Return validation errors if the data is invalid
        return Response({
            "status": "error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(generics.CreateAPIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'detail': 'Both email and password are required',
                'code': 'missing_credentials'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        user = authenticate(request, email=email, password=password)

        
        if user:
            is_blocked = BlockedStudents.objects.filter(email=email).exists()
            if is_blocked:
                return Response({
                    'detail': 'No account found with this email. If you think it\'s a mistake, please contact the admin.',
                    'code': 'user_not_found'
                }, status=status.HTTP_401_UNAUTHORIZED)
            if not user.is_active:
                return Response({
                    'detail': 'Your account is not active.',
                    'code': 'account_inactive'
                }, status=status.HTTP_401_UNAUTHORIZED)
            return user.generate_login_response()
            
        else:
            try:
                print("Hello Wiore", email)
                user = User.objects.get(email=email)
                print("User", user)
                is_blocked = BlockedStudents.objects.filter(email=email).exists()
                if is_blocked:
                    return Response({
                        'detail': 'No account found with this email. If you think it\'s a mistake, please contact the admin.',
                        'code': 'user_not_found'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                return Response({
                    'detail': 'Invalid password. Please try again.',
                    'code': 'invalid_password'
                }, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({
                    'detail': 'No account found with this email. If you think it\'s a mistake, please contact the admin.',
                    'code': 'user_not_found'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
class ProfileAPIView(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = [IsAuthenticated]

    def get(self, request):
        user = get_object_or_404(User, email=request.user.email)

        user_data = {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "gender": user.gender,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "date_joined": user.date_joined,
            "last_login": user.last_login,
            "user_type": user.user_type,
        }

        response_data = {
            "user": user_data,
        }

        if user.user_type == 'student':
            try:
                student = Student.objects.get(student_id=user)
                student_data = {
                    "id": student.id,
                    "batch": student.batch,
                    "current_semester": student.current_semester,
                    "year": student.year,
                    "roll_no": student.roll_no,
                    "student_type": student.student_type,
                    "degree_type": student.degree_type,
                }
                
                if student.dept_id:
                    dept_serializer = DepartmentSerializerForProfile(student.dept_id)
                    student_data["department"] = dept_serializer.data
                
                response_data["student"] = student_data
            except Student.DoesNotExist:
                pass
        
        elif user.user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(teacher_id=user)
                teacher_data = {
                    "id": teacher.id,
                    "staff_code": teacher.staff_code,
                    "teacher_role": teacher.teacher_role,
                    "teacher_specialisation": teacher.teacher_specialisation,
                    "teacher_working_hours": teacher.teacher_working_hours,
                }
                
                if teacher.dept_id:
                    dept_serializer = DepartmentSerializerForProfile(teacher.dept_id)
                    teacher_data["department"] = dept_serializer.data
                
                response_data["teacher"] = teacher_data
            except Teacher.DoesNotExist:
                pass

        return Response({
            "message": "Success",
            "data": response_data
        }, status=status.HTTP_200_OK)

class VerifyTokenAPIView(APIView):
    def get(self, request):
        email = request.query_params.get('email', '')
        token = request.query_params.get('token', '')
        user = get_object_or_404(User, email=email)
        
        try:
            verify = BookingOTP.objects.get(user_id=user, code=token)
            verify.is_verified = True
            verify.save()

            return user.generate_login_response()
        except:
            return Response({'detail': 'Invalid Code.'}, status=status.HTTP_400_BAD_REQUEST)

class AuthStatusAPIView(APIView):
    """Check authentication status and basic user info without requiring auth"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        user_data = {
            'is_authenticated': request.user.is_authenticated,
        }
        
        if request.user.is_authenticated:
            # Add basic user info
            user_data.update({
                'id': request.user.id,
                'email': request.user.email,
                'user_type': request.user.user_type,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            })
            
            # Add student info if applicable
            if request.user.user_type == 'student':
                try:
                    student = Student.objects.get(student_id=request.user)
                    user_data['student_profile'] = {
                        'id': student.id,
                        'has_department': student.dept_id is not None,
                        'department_id': student.dept_id.id if student.dept_id else None,
                        'department_name': student.dept_id.dept_name if student.dept_id else None,
                        'current_semester': student.current_semester,
                    }
                except Student.DoesNotExist:
                    user_data['student_profile'] = None
            
            # Add session info
            session_data = {}
            if hasattr(request, 'session'):
                for key in request.session.keys():
                    session_data[key] = request.session[key]
            user_data['session'] = session_data
        
        return Response(user_data)

class ForgotPasswordAPI(generics.GenericAPIView):
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LoginSerializer

    def post(self, request):
        email = request.data.get('email', '')
        password = request.data.get('password', '')
        
        if not email or not password:
            return Response({
                'detail': 'Both email and new password are required',
                'code': 'missing_credentials'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                return Response({
                    'detail': 'Your account is not active. Please verify your email first.',
                    'code': 'account_inactive'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or update ForgetPassword entry
            verification_code = ''.join(random.choices('0123456789', k=6))
            forget_password, created = ForgetPassword.objects.get_or_create(
                user_id=user,
                defaults={'new_password': password, 'code': verification_code}
            )
            if not created:
                forget_password.new_password = password
                forget_password.code = verification_code
                forget_password.save()
                
            # Here would be code to send the email with verification code
            
            return Response({
                'detail': 'Verification code sent to your email',
                'code': 'reset_email_sent'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'detail': 'No account found with this email. Please sign up first.',
                'code': 'user_not_found'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({
                'detail': 'An error occurred while processing your request. Please try again.',
                'code': 'server_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request):
        email = request.query_params.get('email', '')
        token = request.query_params.get('token', '')
        user = get_object_or_404(User, email=email)

        try:
            f = ForgetPassword.objects.get(user_id=user, code=token)
            user.password = f.new_password
            user.save()
            
            return user.generate_login_response()
        except:
            return Response({'detail': 'Invalid Code.'}, status=status.HTTP_400_BAD_REQUEST)
    

class LogoutAPIView(APIView):
    authentication_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        response.delete_cookie('token', domain=settings.COOKIE_DOMAIN)
        return response

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfTokenAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"success": "CSRF cookie set"})