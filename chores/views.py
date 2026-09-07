from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Household, HouseholdMember, Chore, ChoreCompletion, UserPoints
from .serializers import (
    HouseholdSerializer, HouseholdMemberSerializer, ChoreSerializer, 
    ChoreCompletionSerializer, UserPointsSerializer
)


class HouseholdViewSet(viewsets.ModelViewSet):
    """ViewSet for Household management"""
    serializer_class = HouseholdSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return households the user is a member of"""
        return Household.objects.filter(members__user=self.request.user)

    def perform_create(self, serializer):
        """Create a household and add the creator as admin"""
        household = serializer.save(owner=self.request.user)
        HouseholdMember.objects.create(
            household=household,
            user=self.request.user,
            role='admin'
        )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to a household"""
        household = self.get_object()
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        member, created = HouseholdMember.objects.get_or_create(
            household=household,
            user=user,
            defaults={'role': 'member'}
        )
        
        return Response(HouseholdMemberSerializer(member).data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get household statistics"""
        household = self.get_object()
        stats = {
            'total_chores': household.chores.count(),
            'completed_chores': household.chores.filter(completed=True).count(),
            'members': household.members.count(),
            'leaderboard': UserPointsSerializer(
                household.user_points.all().order_by('-total_points'),
                many=True
            ).data
        }
        return Response(stats)


class ChoreViewSet(viewsets.ModelViewSet):
    """ViewSet for Chore management"""
    serializer_class = ChoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return chores from households the user is a member of"""
        return Chore.objects.filter(household__members__user=self.request.user)

    def perform_create(self, serializer):
        """Create a chore"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a chore as complete"""
        chore = self.get_object()
        
        completion = ChoreCompletion.objects.create(
            chore=chore,
            completed_by=request.user,
            points_earned=chore.points
        )
        
        # Update user points
        user_points, created = UserPoints.objects.get_or_create(
            user=request.user,
            household=chore.household,
            defaults={'total_points': 0}
        )
        user_points.total_points += chore.points
        user_points.save()
        
        # Mark chore as completed
        chore.completed = True
        chore.save()
        
        return Response(ChoreCompletionSerializer(completion).data)


from django.contrib.auth.models import User
