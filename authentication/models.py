from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.response import Response
from teacher.models import Teacher
from django.core.exceptions import ValidationError
# from .utils import send_email
import uuid
import jwt

# Create your models here.
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Users require an email field')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)
    
class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', "Male"),
        ('F', 'Female')
    ]
    USER_TYPE = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    username = None
    email = models.EmailField('Email', unique=True, primary_key=True)
    first_name = models.CharField('First Name', max_length=255, blank=False)
    last_name = models.CharField('Last Name', max_length=255, blank=False)
    phone_number = models.CharField('Phone Number', max_length=20)
    gender = models.CharField('Gender', max_length=10, blank=False, choices=GENDER_CHOICES)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_type = models.CharField(default='student', max_length=20, choices=USER_TYPE, blank=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='user',
    )

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def get_name(self):
        if self.last_name:
            return f'{self.first_name} {self.last_name}'
        return f'{self.first_name}'
    
    def generate_login_response(self):
        payload = {
            'id': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'exp': timezone.now() + timezone.timedelta(days=30),
            'iat': timezone.now()
        }
        
        token = jwt.encode(
            payload=payload,
            key=settings.JWT_KEY,
            algorithm='HS256'
        )
        
        user_type = 'student'
        if self.user_type == 'teacher':
            try:
                user_type = Teacher.objects.get(teacher_id=self.email).teacher_role
            except Exception as E:
                print(E)
        
        response = Response({
            'id': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'gender': self.gender,
            'user_type': user_type,
            'detail': 'Login successful!',
        }, status=status.HTTP_200_OK)

        response.set_cookie(key='token', value=token, samesite='Lax', httponly=True, secure=False, domain=settings.COOKIE_DOMAIN)
        return response

class ForgetPassword(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forget_password', null=True)
    new_password = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    
    def __str__(self):
        return f"{self.user_id}"
    
    def save(self, *args, **kwargs):
        if not self.new_password.startswith('pbkdf2_sha256$'):
            self.new_password = make_password(self.new_password)
        super().save(*args, **kwargs)

class BookingOTP(models.Model):
    user_id = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    code = models.CharField(max_length=10)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user_id}"

class BlockedStudents(models.Model):
    email = models.CharField(unique=True, blank=False, max_length=200)
    name = models.CharField(max_length=200, blank=False)
    dept = models.CharField(max_length=50, blank=False)
    year = models.IntegerField(blank=False)