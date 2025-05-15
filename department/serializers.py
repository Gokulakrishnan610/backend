from rest_framework import serializers
from .models import Department

class DepartmentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Department
        fields = [
            'id',
            'dept_name',
            'date_established',
            'contact_info',
            'hod_id',
        ]
        extra_kwargs = {
            'hod_id': {'write_only': True} 
        }

    def validate(self, data):
        hod_id = data.get('hod_id')
        
        if hod_id and hod_id.user_type != 'teacher':
            raise serializers.ValidationError(
                {"hod_id": "Only teachers can be assigned as HOD"}
            )
            
        return data

    def create(self, validated_data):
        return Department.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.dept_name = validated_data.get('dept_name', instance.dept_name)
        instance.date_established = validated_data.get('date_established', instance.date_established)
        instance.contact_info = validated_data.get('contact_info', instance.contact_info)
        instance.hod_id = validated_data.get('hod_id', instance.hod_id)
        instance.save()
        return instance