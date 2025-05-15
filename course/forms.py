from django import forms
from .models import Course
from courseMaster.models import CourseMaster
from rooms.models import Room
from department.models import Department

class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter courses based on user's department
        if user and hasattr(user, 'teacher') and user.teacher.dept:
            self.fields['course'].queryset = CourseMaster.objects.filter(
                course_dept=user.teacher.dept
            )
        
        # Filter rooms based on lab type
        self.fields['lab_pref'].queryset = Room.objects.filter(is_lab=True)
        
        # Set managed_by choices to user's department and course's department
        if user and hasattr(user, 'teacher') and user.teacher.dept:
            course_dept = self.instance.course.course_dept if self.instance and self.instance.course else None
            if course_dept:
                self.fields['managed_by'].queryset = Department.objects.filter(
                    id__in=[user.teacher.dept.id, course_dept.id]
                )
            else:
                self.fields['managed_by'].queryset = Department.objects.filter(
                    id=user.teacher.dept.id
                )

    class Meta:
        model = Course
        fields = [
            'course', 'course_year', 'course_semester', 'lecture_hours',
            'practical_hours', 'tutorial_hours', 'credits', 'managed_by',
            'regulation', 'course_type', 'elective_type', 'lab_type',
            'lab_pref', 'no_of_students'
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'course_year': forms.Select(attrs={'class': 'form-control'}),
            'course_semester': forms.Select(attrs={'class': 'form-control'}),
            'lecture_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'practical_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'tutorial_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
            'managed_by': forms.Select(attrs={'class': 'form-control'}),
            'regulation': forms.TextInput(attrs={'class': 'form-control'}),
            'course_type': forms.Select(attrs={'class': 'form-control'}),
            'elective_type': forms.Select(attrs={'class': 'form-control'}),
            'lab_type': forms.Select(attrs={'class': 'form-control'}),
            'lab_pref': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'no_of_students': forms.NumberInput(attrs={'class': 'form-control'}),
        } 