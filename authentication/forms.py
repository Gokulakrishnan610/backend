from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from student.models import Student
from teacher.models import Teacher

class CustomUserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2')

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'
        exclude = ('user',)

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = '__all__'
        exclude = ('user',)