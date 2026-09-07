from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Household, HouseholdMember, Chore, ChoreCompletion, UserPoints


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'username']


class HouseholdMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = HouseholdMember
        fields = ['id', 'user', 'role', 'joined_at']


class HouseholdSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = HouseholdMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Household
        fields = ['id', 'name', 'owner', 'members', 'created_at', 'updated_at']


class ChoreCompletionSerializer(serializers.ModelSerializer):
    completed_by = UserSerializer(read_only=True)

    class Meta:
        model = ChoreCompletion
        fields = ['id', 'completed_by', 'completed_at', 'points_earned']


class ChoreSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    completions = ChoreCompletionSerializer(many=True, read_only=True)

    class Meta:
        model = Chore
        fields = ['id', 'household', 'title', 'description', 'assigned_to', 'points', 
                  'frequency', 'due_date', 'created_by', 'created_at', 'updated_at', 
                  'completed', 'completions']


class UserPointsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserPoints
        fields = ['id', 'user', 'total_points', 'last_updated']
