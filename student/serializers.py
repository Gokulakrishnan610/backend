# serializers.py
from rest_framework import serializers
from .models import Student
from authentication.serializers import UserSerializer
from department.serializers import DepartmentSerializer
from authentication.models import User

class StudentSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student_id', read_only=True)
    dept_detail = DepartmentSerializer(source='dept_id', read_only=True)
    email = serializers.EmailField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    phone_number = serializers.CharField(write_only=True, required=False)
    gender = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Student
        fields = [
            'id',
            'student_id',
            'student_detail',
            'batch',
            'current_semester',
            'year',
            'dept_id',
            'dept_detail',
            'roll_no',
            'student_type',
            'degree_type',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'gender'
        ]
        extra_kwargs = {
            'student_id': {'read_only': True}
        }

    def validate(self, data):
        instance = self.instance

        # If updating an existing instance
        if instance:
            student_user = getattr(instance, 'student_id', None)
            batch = data.get('batch', getattr(instance, 'batch', None))
            current_semester = data.get('current_semester', getattr(instance, 'current_semester', None))
            
            if Student.objects.filter(student_id=student_user, batch=batch).exclude(pk=getattr(instance, 'pk', None)).exists():
                raise serializers.ValidationError({"batch": "This student already exists in the specified batch"})
        # If creating a new instance
        else:
            # Validate email is not already in use
            email = data.get('email')
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError({"email": "This email is already in use"})
            
            batch = data.get('batch')
            current_semester = data.get('current_semester')

        if current_semester is not None and (current_semester < 1 or current_semester > 10):
            raise serializers.ValidationError({"current_semester": "Semester must be between 1 and 10"})

        return data

    def create(self, validated_data):
        # Extract user data
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        phone_number = validated_data.pop('phone_number')
        gender = validated_data.pop('gender')
        
        # Create the user with default password
        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            gender=gender,
            user_type='student',
            password='changeme@123'  # Default password
        )
        
        # Create student profile linked to the user
        validated_data['student_id'] = user
        return Student.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Extract user data if present
        user_fields = {}
        for field in ['email', 'first_name', 'last_name', 'phone_number', 'gender']:
            if field in validated_data:
                user_fields[field] = validated_data.pop(field)
        
        # Update user if we have user fields to update
        if user_fields and instance.student_id:
            user = instance.student_id
            for key, value in user_fields.items():
                setattr(user, key, value)
            user.save()
        
        # Update student instance fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        instance.save()
        return instance
