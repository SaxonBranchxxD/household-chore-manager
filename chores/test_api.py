from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from chores.models import Household, HouseholdMember, Chore, UserPoints
from django.utils import timezone
from datetime import timedelta


class UserRegistrationTests(APITestCase):
    """Tests for user registration endpoint"""

    def test_user_registration_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'testpass123'
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_user_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password2': 'differentpass123'
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'testpass123',
            'password2': 'testpass123'
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_missing_fields(self):
        """Test registration with missing fields"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com'
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTests(APITestCase):
    """Tests for user login endpoint"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        """Test successful login"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        """Test login with wrong password"""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        data = {
            'email': 'test@example.com'
        }
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAuthenticationTests(APITestCase):
    """Tests for JWT authentication"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()

    def test_jwt_token_generation(self):
        """Test JWT token generation"""
        refresh = RefreshToken.for_user(self.user)
        self.assertIsNotNone(refresh)
        self.assertIsNotNone(str(refresh.access_token))

    def test_jwt_token_validation(self):
        """Test JWT token validation"""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token_rejected(self):
        """Test that invalid token is rejected"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_token_rejected(self):
        """Test that missing token is rejected"""
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Test token refresh functionality"""
        refresh = RefreshToken.for_user(self.user)
        refresh_token = str(refresh)
        
        data = {'refresh': refresh_token}
        response = self.client.post(reverse('token_refresh'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class HouseholdAPITests(APITestCase):
    """Tests for Household API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_household(self):
        """Test creating a household"""
        data = {'name': 'My Household'}
        response = self.client.post(reverse('household-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'My Household')

    def test_household_creator_becomes_admin(self):
        """Test that creator becomes admin"""
        data = {'name': 'My Household'}
        response = self.client.post(reverse('household-list'), data, format='json')
        household_id = response.data['id']
        
        household = Household.objects.get(id=household_id)
        member = HouseholdMember.objects.get(household=household, user=self.user)
        self.assertEqual(member.role, 'admin')

    def test_list_user_households(self):
        """Test listing user's households"""
        Household.objects.create(name='Household 1', owner=self.user)
        Household.objects.create(name='Household 2', owner=self.user)
        Household.objects.create(name='Other Household', owner=self.other_user)
        
        response = self.client.get(reverse('household-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_household_details(self):
        """Test getting household details"""
        household = Household.objects.create(name='My Household', owner=self.user)
        HouseholdMember.objects.create(household=household, user=self.user, role='admin')
        
        response = self.client.get(reverse('household-detail', args=[household.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'My Household')

    def test_update_household(self):
        """Test updating a household"""
        household = Household.objects.create(name='My Household', owner=self.user)
        HouseholdMember.objects.create(household=household, user=self.user, role='admin')
        
        data = {'name': 'Updated Household'}
        response = self.client.patch(
            reverse('household-detail', args=[household.id]),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Household')

    def test_add_member_to_household(self):
        """Test adding a member to household"""
        household = Household.objects.create(name='My Household', owner=self.user)
        HouseholdMember.objects.create(household=household, user=self.user, role='admin')
        
        data = {'email': self.other_user.email}
        response = self.client.post(
            reverse('household-add-member', args=[household.id]),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            HouseholdMember.objects.filter(
                household=household,
                user=self.other_user
            ).exists()
        )

    def test_get_household_stats(self):
        """Test getting household statistics"""
        household = Household.objects.create(name='My Household', owner=self.user)
        HouseholdMember.objects.create(household=household, user=self.user, role='admin')
        
        response = self.client.get(
            reverse('household-stats', args=[household.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_chores', response.data)
        self.assertIn('completed_chores', response.data)
        self.assertIn('members', response.data)
        self.assertIn('leaderboard', response.data)


class ChoreAPITests(APITestCase):
    """Tests for Chore API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assigned_user = User.objects.create_user(
            username='assigned',
            email='assigned@example.com',
            password='testpass123'
        )
        self.household = Household.objects.create(name='My Household', owner=self.user)
        HouseholdMember.objects.create(household=self.household, user=self.user, role='admin')
        HouseholdMember.objects.create(household=self.household, user=self.assigned_user, role='member')
        
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_chore(self):
        """Test creating a chore"""
        data = {
            'household': self.household.id,
            'title': 'Clean Kitchen',
            'description': 'Clean all surfaces',
            'assigned_to': self.assigned_user.id,
            'points': 15,
            'frequency': 'once',
            'due_date': (timezone.now() + timedelta(days=1)).isoformat()
        }
        response = self.client.post(reverse('chore-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Clean Kitchen')

    def test_list_chores(self):
        """Test listing chores"""
        due_date = timezone.now() + timedelta(days=1)
        Chore.objects.create(
            household=self.household,
            title='Chore 1',
            due_date=due_date,
            created_by=self.user
        )
        Chore.objects.create(
            household=self.household,
            title='Chore 2',
            due_date=due_date,
            created_by=self.user
        )
        
        response = self.client.get(reverse('chore-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_chore_details(self):
        """Test getting chore details"""
        due_date = timezone.now() + timedelta(days=1)
        chore = Chore.objects.create(
            household=self.household,
            title='Clean Kitchen',
            due_date=due_date,
            created_by=self.user
        )
        
        response = self.client.get(reverse('chore-detail', args=[chore.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Clean Kitchen')

    def test_update_chore(self):
        """Test updating a chore"""
        due_date = timezone.now() + timedelta(days=1)
        chore = Chore.objects.create(
            household=self.household,
            title='Clean Kitchen',
            due_date=due_date,
            created_by=self.user
        )
        
        data = {'title': 'Clean Bathroom'}
        response = self.client.patch(
            reverse('chore-detail', args=[chore.id]),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Clean Bathroom')

    def test_delete_chore(self):
        """Test deleting a chore"""
        due_date = timezone.now() + timedelta(days=1)
        chore = Chore.objects.create(
            household=self.household,
            title='Clean Kitchen',
            due_date=due_date,
            created_by=self.user
        )
        
        response = self.client.delete(reverse('chore-detail', args=[chore.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Chore.objects.filter(id=chore.id).exists())


class ChoreCompletionTests(APITestCase):
    """Tests for Chore completion and points system"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.completed_user = User.objects.create_user(
            username='completed',
            email='completed@example.com',
            password='testpass123'
        )
        self.household = Household.objects.create(name='My Household', owner=self.user)
        HouseholdMember.objects.create(household=self.household, user=self.user, role='admin')
        HouseholdMember.objects.create(household=self.household, user=self.completed_user, role='member')
        
        self.chore = Chore.objects.create(
            household=self.household,
            title='Clean Kitchen',
            points=20,
            due_date=timezone.now() + timedelta(days=1),
            created_by=self.user
        )
        
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.completed_user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_mark_chore_complete(self):
        """Test marking a chore as complete"""
        response = self.client.post(
            reverse('chore-complete', args=[self.chore.id]),
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.chore.refresh_from_db()
        self.assertTrue(self.chore.completed)

    def test_points_awarded_on_completion(self):
        """Test that points are awarded on completion"""
        self.client.post(
            reverse('chore-complete', args=[self.chore.id]),
            format='json'
        )
        
        user_points = UserPoints.objects.get(user=self.completed_user, household=self.household)
        self.assertEqual(user_points.total_points, 20)

    def test_completion_recorded(self):
        """Test that completion is recorded"""
        self.client.post(
            reverse('chore-complete', args=[self.chore.id]),
            format='json'
        )
        
        self.assertTrue(
            ChoreCompletion.objects.filter(
                chore=self.chore,
                completed_by=self.completed_user,
                points_earned=20
            ).exists()
        )

    def test_leaderboard_ranking(self):
        """Test leaderboard ranks users by points"""
        # Create another user with fewer points
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        HouseholdMember.objects.create(household=self.household, user=other_user, role='member')
        UserPoints.objects.create(user=other_user, household=self.household, total_points=5)
        
        # Complete chore to get 20 points
        self.client.post(
            reverse('chore-complete', args=[self.chore.id]),
            format='json'
        )
        
        # Get household stats
        refresh = RefreshToken.for_user(self.user)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('household-stats', args=[self.household.id])
        )
        
        leaderboard = response.data['leaderboard']
        self.assertEqual(len(leaderboard), 2)
        self.assertEqual(leaderboard[0]['total_points'], 20)
        self.assertEqual(leaderboard[1]['total_points'], 5)

    def test_multiple_completions_accumulate_points(self):
        """Test that multiple completions accumulate points"""
        # First completion
        self.client.post(
            reverse('chore-complete', args=[self.chore.id]),
            format='json'
        )
        
        # Create another chore and complete it
        chore2 = Chore.objects.create(
            household=self.household,
            title='Water Plants',
            points=10,
            due_date=timezone.now() + timedelta(days=1),
            created_by=self.user
        )
        
        self.client.post(
            reverse('chore-complete', args=[chore2.id]),
            format='json'
        )
        
        user_points = UserPoints.objects.get(user=self.completed_user, household=self.household)
        self.assertEqual(user_points.total_points, 30)
