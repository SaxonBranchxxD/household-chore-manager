from rest_framework import serializers
from django.contrib.auth.models import User
from chores.models import Household, HouseholdMember, Chore, ChoreCompletion, UserPoints


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                if not user.check_password(password):
                    raise serializers.ValidationError("Invalid credentials.")
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials.")
        else:
            raise serializers.ValidationError("Email and password are required.")

        data['user'] = user
        return data


class HouseholdMemberSerializer(serializers.ModelSerializer):
    """Serializer for Household Members"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = HouseholdMember
        fields = ('id', 'user', 'username', 'user_email', 'role', 'joined_at')
        read_only_fields = ('id', 'joined_at')


class ChoreSerializer(serializers.ModelSerializer):
    """Serializer for Chore model"""
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    completion_count = serializers.SerializerMethodField()

    class Meta:
        model = Chore
        fields = (
            'id', 'household', 'title', 'description', 'assigned_to', 
            'assigned_to_email', 'points', 'frequency', 'due_date', 
            'created_by', 'created_by_email', 'completed', 'completion_count',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'completion_count')

    def get_completion_count(self, obj):
        return obj.completions.count()


class ChoreCompletionSerializer(serializers.ModelSerializer):
    """Serializer for ChoreCompletion model"""
    completed_by_email = serializers.EmailField(source='completed_by.email', read_only=True)
    chore_title = serializers.CharField(source='chore.title', read_only=True)

    class Meta:
        model = ChoreCompletion
        fields = ('id', 'chore', 'chore_title', 'completed_by', 'completed_by_email', 
                 'points_earned', 'completed_at')
        read_only_fields = ('id', 'completed_at')


class UserPointsSerializer(serializers.ModelSerializer):
    """Serializer for UserPoints model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    household_name = serializers.CharField(source='household.name', read_only=True)

    class Meta:
        model = UserPoints
        fields = ('id', 'user', 'user_email', 'username', 'household', 'household_name',
                 'total_points', 'last_updated')
        read_only_fields = ('id', 'last_updated')


class HouseholdSerializer(serializers.ModelSerializer):
    """Serializer for Household model"""
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    members = HouseholdMemberSerializer(many=True, read_only=True, source='members.all')
    member_count = serializers.SerializerMethodField()
    chore_count = serializers.SerializerMethodField()

    class Meta:
        model = Household
        fields = ('id', 'name', 'owner', 'owner_email', 'members', 'member_count',
                 'chore_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'owner', 'members', 'created_at', 'updated_at')

    def get_member_count(self, obj):
        return obj.members.count()

    def get_chore_count(self, obj):
        return obj.chores.count()
