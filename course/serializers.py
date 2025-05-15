from rest_framework import serializers
from .models import Course, CourseResourceAllocation, CourseSlotPreference, CourseRoomPreference
from department.serializers import DepartmentSerializer
from courseMaster.serializers import CourseMasterSerializer
from slot.serializers import SlotSerializer
from rooms.serializers import RoomSerializer

class StudentCourseListSerializer(serializers.ModelSerializer):
    """A simplified serializer for student course selection with just the essential fields"""
    # Get basic course details from CourseMaster
    course_code = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    credits = serializers.SerializerMethodField()
    course_type = serializers.SerializerMethodField()
    # Department info
    dept_name = serializers.SerializerMethodField()
    teaching_dept_name = serializers.SerializerMethodField()
    course_description = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id',
            'course_code',
            'course_name',
            'credits',
            'course_type',
            'course_year',
            'course_semester',
            'dept_name',
            'teaching_dept_name',
            'elective_type',
            'course_description',
        ]
    
    def get_course_code(self, obj):
        try:
            if obj.course_id and hasattr(obj.course_id, 'course_id'):
                return obj.course_id.course_id
        except:
            pass
        return "Unknown Code"
    
    def get_course_name(self, obj):
        try:
            if obj.course_id and hasattr(obj.course_id, 'course_name'):
                return obj.course_id.course_name
        except:
            pass
        return "Unnamed Course"
    
    def get_credits(self, obj):
        try:
            if obj.course_id and hasattr(obj.course_id, 'credits'):
                return obj.course_id.credits
        except:
            pass
        return 0
    
    def get_course_type(self, obj):
        try:
            if obj.course_id and hasattr(obj.course_id, 'course_type'):
                return obj.course_id.course_type
        except:
            pass
        return "T"
    
    def get_dept_name(self, obj):
        try:
            if obj.for_dept_id and hasattr(obj.for_dept_id, 'dept_name'):
                return obj.for_dept_id.dept_name
        except:
            pass
        return "Unknown Department"
    
    def get_teaching_dept_name(self, obj):
        try:
            if obj.teaching_dept_id and hasattr(obj.teaching_dept_id, 'dept_name'):
                return obj.teaching_dept_id.dept_name
        except:
            pass
        return "Unknown Teaching Department"
    
    def get_course_description(self, obj):
        """Generate a description from available data"""
        try:
            # Map course type
            course_type_map = {
                'T': 'Theory',
                'L': 'Lab',
                'LoT': 'Lab and Theory'
            }
            
            # Map elective type
            elective_type_map = {
                'NE': 'Core Course',
                'PE': 'Professional Elective',
                'OE': 'Open Elective'
            }
            
            # Get values with fallbacks
            course_type = "Course"
            try:
                if obj.course_id and hasattr(obj.course_id, 'course_type'):
                    course_type = course_type_map.get(obj.course_id.course_type, 'Course')
            except:
                pass
            
            elective_type = ""
            try:
                if hasattr(obj, 'elective_type'):
                    elective_type = elective_type_map.get(obj.elective_type, '')
            except:
                pass
            
            # Build description
            description = f"{course_type}"
            if elective_type:
                description += f" ({elective_type})"
            
            # Add teaching department if different
            try:
                if (obj.teaching_dept_id and obj.for_dept_id and 
                    obj.teaching_dept_id != obj.for_dept_id):
                    description += f". Taught by {obj.teaching_dept_id.dept_name} department."
            except:
                pass
                
            # Add year and semester
            try:
                description += f" Year {obj.course_year}, Semester {obj.course_semester}."
            except:
                pass
                
            return description
        except Exception as e:
            # Fallback for any unexpected errors
            import logging
            logger = logging.getLogger('django')
            logger.error(f"Error generating course description: {str(e)}")
            
            # Use the course ID if available, otherwise a generic description
            try:
                if obj.course_id and hasattr(obj.course_id, 'course_name'):
                    return f"Course: {obj.course_id.course_name}"
            except:
                pass
                
            return "Course information"

class CourseSerializer(serializers.ModelSerializer):
    course_detail = CourseMasterSerializer(source='course_id', read_only=True)
    for_dept_detail = DepartmentSerializer(source='for_dept_id', read_only=True)
    teaching_dept_detail = DepartmentSerializer(source='teaching_dept_id', read_only=True)
    relationship_type = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    # Proxy fields from CourseMaster
    lecture_hours = serializers.IntegerField(source='course_id.lecture_hours', read_only=True)
    tutorial_hours = serializers.IntegerField(source='course_id.tutorial_hours', read_only=True)
    practical_hours = serializers.IntegerField(source='course_id.practical_hours', read_only=True)
    credits = serializers.IntegerField(source='course_id.credits', read_only=True)
    regulation = serializers.CharField(source='course_id.regulation', read_only=True)
    course_type = serializers.CharField(source='course_id.course_type', read_only=True)
    is_zero_credit_course = serializers.BooleanField(source='course_id.is_zero_credit_course', read_only=True)
    no_of_students = serializers.IntegerField(default=0, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id',
            'course_id',
            'course_detail',
            'course_year',
            'course_semester',
            'lecture_hours',
            'tutorial_hours',
            'practical_hours',
            'credits',
            'for_dept_id',
            'for_dept_detail',
            'teaching_dept_id',
            'teaching_dept_detail',
            'need_assist_teacher',
            'regulation',
            'course_type',
            'elective_type',
            'lab_type',
            'no_of_students',
            'is_zero_credit_course',
            'teaching_status',
            'relationship_type',
            'permissions'
        ]
    
    def get_permissions(self, obj):
        """
        Determine what permissions the current user has for this course.
        
        Returns a dictionary of permissions based on the user's department role:
        - can_edit: Whether the user can edit this course
        - can_delete: Whether the user can delete this course
        - editable_fields: List of fields the user can edit (if can_edit is True)
        """
        request = self.context.get('request')
        if not request or not request.user:
            return {
                'can_edit': False,
                'can_delete': False,
                'editable_fields': []
            }
            
        # Get user's department (if HOD)
        user_dept = None
        try:
            from department.models import Department
            user_dept = Department.objects.filter(hod_id=request.user).first()
        except:
            pass
            
        if not user_dept:
            return {
                'can_edit': False,
                'can_delete': False,
                'editable_fields': []
            }
            
        # Get department relationships
        owning_dept_id = obj.course_id.course_dept_id.id if obj.course_id and obj.course_id.course_dept_id else None
        for_dept_id = obj.for_dept_id.id if obj.for_dept_id else None
        teaching_dept_id = obj.teaching_dept_id.id if obj.teaching_dept_id else None
        
        # Owner department - full rights (edit and delete)
        is_owner = user_dept.id == owning_dept_id
        
        # Teaching department - limited edit rights, now also has delete rights
        is_teacher = user_dept.id == teaching_dept_id if teaching_dept_id else False
        
        # For department - only delete rights, no edit rights
        is_learner = user_dept.id == for_dept_id if for_dept_id else False
        
        # Owner or teaching department can edit
        can_edit = is_owner or is_teacher
        
        # Owner, teaching department, or for department can delete
        can_delete = is_owner or is_teacher or is_learner
        
        # Determine which fields can be edited based on role
        editable_fields = []
        if is_owner:
            # Owner can edit all fields except those now in CourseMaster and dept assignments
            editable_fields = [
                'course_year', 'course_semester',
                'need_assist_teacher',
                'elective_type', 'lab_type', 'teaching_status'
            ]
        elif is_teacher:
            editable_fields = ['teaching_status', 'course_year', 'course_semester', 'need_assist_teacher']
        
        return {
            'can_edit': can_edit,
            'can_delete': can_delete,
            'editable_fields': editable_fields
        }
    
    def get_relationship_type(self, obj):
        """
        Determine the relationship type between departments for this course:
        
        OWNING DEPARTMENT: Department that created and maintains the course curriculum
        FOR DEPARTMENT: Department whose students will take this course
        TEACHING DEPARTMENT: Department responsible for providing teachers and teaching the course
        
        1. SELF_OWNED_SELF_TAUGHT: course owned by dept X, for dept X, taught by dept X
        2. SELF_OWNED_OTHER_TAUGHT: course owned by dept X, for dept X, taught by dept Y
        3. OTHER_OWNED_SELF_TAUGHT: course owned by dept Y, for dept X, taught by dept X
        4. OTHER_OWNED_OTHER_TAUGHT: course owned by dept Y, for dept X, taught by dept Z
        5. SELF_OWNED_FOR_OTHER_SELF_TAUGHT: course owned by dept X, for dept Y, taught by dept X
        6. SELF_OWNED_FOR_OTHER_OTHER_TAUGHT: course owned by dept X, for dept Y, taught by dept Z
        """
        owning_dept_id = obj.course_id.course_dept_id.id if obj.course_id and obj.course_id.course_dept_id else None
        for_dept_id = obj.for_dept_id.id if obj.for_dept_id else None
        teaching_dept_id = obj.teaching_dept_id.id if obj.teaching_dept_id else None
        
        if owning_dept_id == for_dept_id == teaching_dept_id:
            return {
                "code": "SELF_OWNED_SELF_TAUGHT",
                "description": "This course is owned, taught, and taken by the same department. The department controls the curriculum, provides teachers, and its students take this course."
            }
            
        elif owning_dept_id == for_dept_id and owning_dept_id != teaching_dept_id:
            return {
                "code": "SELF_OWNED_OTHER_TAUGHT",
                "description": "This course belongs to and is taken by this department, but the teaching is done by another department's faculty."
            }
            
        elif owning_dept_id != for_dept_id and for_dept_id == teaching_dept_id:
            return {
                "code": "OTHER_OWNED_SELF_TAUGHT",
                "description": "This course is owned by another department that controls the curriculum, but this department's students take the course and it's taught by this department's faculty."
            }
            
        elif owning_dept_id != for_dept_id and owning_dept_id != teaching_dept_id and for_dept_id != teaching_dept_id:
            return {
                "code": "OTHER_OWNED_OTHER_TAUGHT",
                "description": "This course is owned by one department, taken by this department's students, and taught by a third department's faculty."
            }
            
        elif owning_dept_id == teaching_dept_id and owning_dept_id != for_dept_id:
            return {
                "code": "SELF_OWNED_FOR_OTHER_SELF_TAUGHT",
                "description": "This course is owned and taught by this department, but provided as a service to another department's students."
            }
            
        elif owning_dept_id != teaching_dept_id and owning_dept_id != for_dept_id and for_dept_id != teaching_dept_id:
            return {
                "code": "SELF_OWNED_FOR_OTHER_OTHER_TAUGHT",
                "description": "This course is owned by this department, taken by another department's students, and taught by a third department's faculty."
            }
            
        return {
            "code": "UNKNOWN",
            "description": "Unknown relationship type"
        }
        
    def validate(self, data):
        for_dept_id = data.get('for_dept_id', self.instance.for_dept_id if self.instance else None)
        course_id = data.get('course_id', self.instance.course_id if self.instance else None)
        course_semester = data.get('course_semester', self.instance.course_semester if self.instance else None)
        teaching_dept_id = data.get('teaching_dept_id', self.instance.teaching_dept_id if self.instance else None)

        if Course.objects.filter(
            for_dept_id=for_dept_id,
            course_id=course_id,
            course_semester=course_semester,
            teaching_dept_id=teaching_dept_id
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError(
                "A course with these details already exists."
            )
        
        return data

class CourseSlotPreferenceSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source='course_id', read_only=True)
    slot_detail = SlotSerializer(source='slot_id', read_only=True)
    
    class Meta:
        model = CourseSlotPreference
        fields = [
            'id',
            'course_id',
            'course_detail',
            'slot_id',
            'slot_detail',
            'preference_level'
        ]

class CourseRoomPreferenceSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source='course_id', read_only=True)
    room_detail = RoomSerializer(source='room_id', read_only=True)
    
    class Meta:
        model = CourseRoomPreference
        fields = [
            'id',
            'course_id',
            'course_detail',
            'room_id',
            'room_detail',
            'preference_level',
            'preferred_for',
            'tech_level_preference',
            'lab_type',
            'lab_description'
        ]
        
    def validate(self, data):
        preferred_for = data.get('preferred_for')
        
        # If technical lab is selected, lab_type should be provided
        if preferred_for == 'TL' and not data.get('lab_type'):
            raise serializers.ValidationError({
                'detail': 'Lab type is required for technical labs',
                'code': 'invalid_lab_type'
            })
            
        # Update tech_level_preference based on lab_type for technical labs
        if preferred_for == 'TL' and data.get('lab_type'):
            lab_type_to_tech_level = {
                'low-end': 'Basic',
                'mid-end': 'Advanced',
                'high-end': 'High-tech'
            }
            data['tech_level_preference'] = lab_type_to_tech_level.get(data['lab_type'], 'Basic')
            
            # Set default lab description if not provided
            if not data.get('lab_description'):
                lab_descriptions = {
                    'low-end': 'For programming subjects, basic coding, and web development',
                    'mid-end': 'For OS, database, and computation-intensive subjects',
                    'high-end': 'For ML, NLP, graphics, design, and resource-intensive subjects'
                }
                data['lab_description'] = lab_descriptions.get(data['lab_type'], '')
        
        # Only require room_id for Non-Technical Lab
        if preferred_for == 'NTL' and not data.get('room_id'):
            raise serializers.ValidationError({
                'detail': 'Room selection is required for non-technical labs',
                'code': 'missing_room'
            })
        
        # For GENERAL and TL, room_id is optional (we'll use the course's associated rooms)
        if preferred_for in ['GENERAL', 'TL'] and not data.get('room_id'):
            # Set a default placeholder value to pass model validation
            data['room_id'] = None
        
        return data

class CourseResourceAllocationSerializer(serializers.ModelSerializer):
    course_detail = serializers.SerializerMethodField()
    original_dept_detail = DepartmentSerializer(source='original_dept_id', read_only=True)
    teaching_dept_detail = DepartmentSerializer(source='teaching_dept_id', read_only=True)
    
    class Meta:
        model = CourseResourceAllocation
        fields = [
            'id',
            'course_id',
            'course_detail',
            'original_dept_id',
            'original_dept_detail',
            'teaching_dept_id',
            'teaching_dept_detail',
            'allocation_reason',
            'allocation_date',
            'status'
        ]
    
    def get_course_detail(self, obj):
        if obj.course_id:
            return CourseSerializer(obj.course_id, context=self.context).data
        return None

class CreateCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'course_id',
            'course_year',
            'course_semester',
            'for_dept_id',
            'teaching_dept_id',
            'need_assist_teacher',
            'elective_type',
            'lab_type',
            'teaching_status'
        ]

    def validate(self, data):
        course_id = data.get('course_id')
        for_dept_id = data.get('for_dept_id')
        course_semester = data.get('course_semester')
        teaching_dept_id = data.get('teaching_dept_id')

        if Course.objects.filter(
            course_id=course_id,
            for_dept_id=for_dept_id,
            course_semester=course_semester,
            teaching_dept_id=teaching_dept_id
        ).exists():
            raise serializers.ValidationError(
                "A course with these details already exists."
            )
        
        return data

class UpdateCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'course_year',
            'course_semester',
            'for_dept_id',
            'teaching_dept_id',
            'need_assist_teacher',
            'elective_type',
            'lab_type',
            'teaching_status'
        ]

    def validate(self, data):
        instance = self.instance
        course_id = instance.course_id
        for_dept_id = data.get('for_dept_id', instance.for_dept_id)
        course_semester = data.get('course_semester', instance.course_semester)
        teaching_dept_id = data.get('teaching_dept_id', instance.teaching_dept_id)

        if Course.objects.filter(
            course_id=course_id,
            for_dept_id=for_dept_id,
            course_semester=course_semester,
            teaching_dept_id=teaching_dept_id
        ).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError(
                "A course with these details already exists."
            )
        
        return data