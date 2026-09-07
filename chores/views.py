from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Household, HouseholdMember, Chore, ChoreCompletion, UserPoints
from .serializers import (
    HouseholdSerializer, HouseholdMemberSerializer, ChoreSerializer, 
    ChoreCompletionSerializer, UserPointsSerializer, UserSerializer,
    UserRegistrationSerializer, UserLoginSerializer
)


# Authentication Endpoints
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {'message': 'User registered successfully'},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint - returns JWT tokens"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get current user profile"""
    user = request.user
    return Response(UserSerializer(user).data)


# ViewSets
class HouseholdViewSet(viewsets.ModelViewSet):
    """ViewSet for Household management"""
    serializer_class = HouseholdSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return households the user is a member of"""
        return Household.objects.filter(members__user=self.request.user).distinct()

    def perform_create(self, serializer):
        """Create a household and add the creator as admin"""
        household = serializer.save(owner=self.request.user)
        HouseholdMember.objects.create(
            household=household,
            user=self.request.user,
            role='admin'
        )
        # Initialize user points for the creator
        UserPoints.objects.get_or_create(
            user=self.request.user,
            household=household,
            defaults={'total_points': 0}
        )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to a household"""
        household = self.get_object()
        
        # Check if user is admin
        member_obj = HouseholdMember.objects.filter(household=household, user=request.user).first()
        if not member_obj or member_obj.role != 'admin':
            return Response(
                {'error': 'Only admins can add members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is already a member
        if HouseholdMember.objects.filter(household=household, user=user).exists():
            return Response(
                {'error': 'User is already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member = HouseholdMember.objects.create(
            household=household,
            user=user,
            role='member'
        )
        
        # Initialize user points for the new member
        UserPoints.objects.get_or_create(
            user=user,
            household=household,
            defaults={'total_points': 0}
        )
        
        return Response(HouseholdMemberSerializer(member).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get household statistics and leaderboard"""
        household = self.get_object()
        
        # Check if user is a member
        if not HouseholdMember.objects.filter(household=household, user=request.user).exists():
            return Response(
                {'error': 'Not a member of this household'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        leaderboard = UserPoints.objects.filter(household=household).order_by('-total_points')
        
        stats = {
            'total_chores': household.chores.count(),
            'completed_chores': household.chores.filter(completed=True).count(),
            'members': household.members.count(),
            'leaderboard': UserPointsSerializer(leaderboard, many=True).data
        }
        return Response(stats)


class ChoreViewSet(viewsets.ModelViewSet):
    """ViewSet for Chore management"""
    serializer_class = ChoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return chores from households the user is a member of"""
        return Chore.objects.filter(
            household__members__user=self.request.user
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        """Create a chore"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Update a chore"""
        serializer.save()

    def perform_destroy(self, instance):
        """Delete a chore"""
        instance.delete()

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a chore as complete"""
        chore = self.get_object()
        
        # Check if user is a member of the household
        if not HouseholdMember.objects.filter(household=chore.household, user=request.user).exists():
            return Response(
                {'error': 'Not a member of this household'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already completed
        if chore.completed:
            return Response(
                {'error': 'Chore is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Record completion
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
        
        return Response(ChoreCompletionSerializer(completion).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def by_household(self, request):
        """Get chores filtered by household"""
        household_id = request.query_params.get('household_id')
        if not household_id:
            return Response(
                {'error': 'household_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        household = get_object_or_404(Household, id=household_id)
        
        # Check if user is a member
        if not HouseholdMember.objects.filter(household=household, user=request.user).exists():
            return Response(
                {'error': 'Not a member of this household'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        chores = self.get_queryset().filter(household=household)
        serializer = self.get_serializer(chores, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending (incomplete) chores"""
        pending_chores = self.get_queryset().filter(completed=False).order_by('due_date')
        serializer = self.get_serializer(pending_chores, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed chores"""
        completed_chores = self.get_queryset().filter(completed=True).order_by('-updated_at')
        serializer = self.get_serializer(completed_chores, many=True)
        return Response(serializer.data)


class UserPointsViewSet(viewsets.ViewSet):
    """ViewSet for User Points"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_points(self, request):
        """Get current user's points across all households"""
        user_points = UserPoints.objects.filter(user=request.user).order_by('-total_points')
        serializer = UserPointsSerializer(user_points, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def household_leaderboard(self, request):
        """Get leaderboard for a specific household"""
        household_id = request.query_params.get('household_id')
        if not household_id:
            return Response(
                {'error': 'household_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        household = get_object_or_404(Household, id=household_id)
        
        # Check if user is a member
        if not HouseholdMember.objects.filter(household=household, user=request.user).exists():
            return Response(
                {'error': 'Not a member of this household'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        leaderboard = UserPoints.objects.filter(
            household=household
        ).order_by('-total_points')
        serializer = UserPointsSerializer(leaderboard, many=True)
        return Response(serializer.data)
