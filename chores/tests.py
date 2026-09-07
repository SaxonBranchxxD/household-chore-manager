from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from chores.models import Household, HouseholdMember, Chore, ChoreCompletion, UserPoints


class HouseholdModelTests(TestCase):
    """Tests for Household model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_household(self):
        """Test creating a household"""
        household = Household.objects.create(
            name='Test Household',
            owner=self.user
        )
        self.assertEqual(household.name, 'Test Household')
        self.assertEqual(household.owner, self.user)

    def test_household_str_representation(self):
        """Test household string representation"""
        household = Household.objects.create(
            name='Test Household',
            owner=self.user
        )
        self.assertEqual(str(household), 'Test Household')

    def test_household_created_at_is_set(self):
        """Test that created_at is automatically set"""
        household = Household.objects.create(
            name='Test Household',
            owner=self.user
        )
        self.assertIsNotNone(household.created_at)

    def test_household_updated_at_is_set(self):
        """Test that updated_at is automatically set"""
        household = Household.objects.create(
            name='Test Household',
            owner=self.user
        )
        self.assertIsNotNone(household.updated_at)


class HouseholdMemberModelTests(TestCase):
    """Tests for HouseholdMember model"""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='testpass123'
        )
        self.household = Household.objects.create(
            name='Test Household',
            owner=self.owner
        )

    def test_create_household_member(self):
        """Test creating a household member"""
        member = HouseholdMember.objects.create(
            household=self.household,
            user=self.member,
            role='member'
        )
        self.assertEqual(member.household, self.household)
        self.assertEqual(member.user, self.member)
        self.assertEqual(member.role, 'member')

    def test_create_admin_member(self):
        """Test creating an admin member"""
        member = HouseholdMember.objects.create(
            household=self.household,
            user=self.member,
            role='admin'
        )
        self.assertEqual(member.role, 'admin')

    def test_unique_constraint_household_user(self):
        """Test that a user can't be added twice to same household"""
        HouseholdMember.objects.create(
            household=self.household,
            user=self.member,
            role='member'
        )
        with self.assertRaises(Exception):
            HouseholdMember.objects.create(
                household=self.household,
                user=self.member,
                role='admin'
            )

    def test_household_member_str_representation(self):
        """Test household member string representation"""
        member = HouseholdMember.objects.create(
            household=self.household,
            user=self.member,
            role='member'
        )
        self.assertIn(self.member.email, str(member))
        self.assertIn(self.household.name, str(member))

    def test_joined_at_is_set(self):
        """Test that joined_at is automatically set"""
        member = HouseholdMember.objects.create(
            household=self.household,
            user=self.member,
            role='member'
        )
        self.assertIsNotNone(member.joined_at)


class ChoreModelTests(TestCase):
    """Tests for Chore model"""

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
        self.household = Household.objects.create(
            name='Test Household',
            owner=self.user
        )
        self.due_date = timezone.now() + timedelta(days=1)

    def test_create_chore(self):
        """Test creating a chore"""
        chore = Chore.objects.create(
            household=self.household,
            title='Clean Kitchen',
            description='Clean all kitchen surfaces',
            assigned_to=self.assigned_user,
            points=10,
            frequency='once',
            due_date=self.due_date,
            created_by=self.user
        )
        self.assertEqual(chore.title, 'Clean Kitchen')
        self.assertEqual(chore.points, 10)
        self.assertEqual(chore.frequency, 'once')
        self.assertFalse(chore.completed)

    def test_create_weekly_chore(self):
        """Test creating a weekly recurring chore"""
        chore = Chore.objects.create(
            household=self.household,
            title='Water Plants',
            frequency='weekly',
            due_date=self.due_date,
            created_by=self.user
        )
        self.assertEqual(chore.frequency, 'weekly')

    def test_chore_str_representation(self):
        """Test chore string representation"""
        chore = Chore.objects.create(
            household=self.household,
            title='Clean Kitchen',
            due_date=self.due_date,
            created_by=self.user
        )
        self.assertEqual(str(chore), 'Clean Kitchen')

    def test_chore_created_at_is_set(self):
        """Test that created_at is automatically set"""
        chore = Chore.objects.create(
            household=self.household,
            title='Clean Kitchen',
            due_date=self.due_date,
            created_by=self.user
        )
        self.assertIsNotNone(chore.created_at)

    def test_chore_default_points(self):
        """Test that chore has default points"""
        chore = Chore.objects.create(
            household=self.household,
            title='Clean Kitchen',
            due_date=self.due_date,
            created_by=self.user
        )
        self.assertEqual(chore.points, 10)


class ChoreCompletionModelTests(TestCase):
    """Tests for ChoreCompletion model"""

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
        self.household = Household.objects.create(
            name='Test Household',
            owner=self.user
        )
        self.chore = Chore.objects.create(
            household=self.household,
            title='Clean Kitchen',
            points=15,
            due_date=timezone.now() + timedelta(days=1),
            created_by=self.user
        )

    def test_create_chore_completion(self):
        """Test recording chore completion"""
        completion = ChoreCompletion.objects.create(
            chore=self.chore,
            completed_by=self.completed_user,
            points_earned=15
        )
        self.assertEqual(completion.chore, self.chore)
        self.assertEqual(completion.completed_by, self.completed_user)
        self.assertEqual(completion.points_earned, 15)

    def test_completed_at_is_set(self):
        """Test that completed_at is automatically set"""
        completion = ChoreCompletion.objects.create(
            chore=self.chore,
            completed_by=self.completed_user,
            points_earned=15
        )
        self.assertIsNotNone(completion.completed_at)

    def test_chore_completion_str_representation(self):
        """Test chore completion string representation"""
        completion = ChoreCompletion.objects.create(
            chore=self.chore,
            completed_by=self.completed_user,
            points_earned=15
        )
        self.assertIn(self.chore.title, str(completion))
        self.assertIn(self.completed_user.email, str(completion))

    def test_multiple_completions_for_same_chore(self):
        """Test that same chore can have multiple completions"""
        ChoreCompletion.objects.create(
            chore=self.chore,
            completed_by=self.completed_user,
            points_earned=15
        )
        completion2 = ChoreCompletion.objects.create(
            chore=self.chore,
            completed_by=self.completed_user,
            points_earned=15
        )
        self.assertEqual(ChoreCompletion.objects.filter(chore=self.chore).count(), 2)


class UserPointsModelTests(TestCase):
    """Tests for UserPoints model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.household = Household.objects.create(
            name='Test Household',
            owner=self.user
        )

    def test_create_user_points(self):
        """Test creating user points record"""
        points = UserPoints.objects.create(
            user=self.user,
            household=self.household,
            total_points=50
        )
        self.assertEqual(points.user, self.user)
        self.assertEqual(points.household, self.household)
        self.assertEqual(points.total_points, 50)

    def test_user_points_default_zero(self):
        """Test that default points are zero"""
        points = UserPoints.objects.create(
            user=self.user,
            household=self.household
        )
        self.assertEqual(points.total_points, 0)

    def test_unique_constraint_user_household(self):
        """Test that a user can only have one points record per household"""
        UserPoints.objects.create(
            user=self.user,
            household=self.household,
            total_points=50
        )
        with self.assertRaises(Exception):
            UserPoints.objects.create(
                user=self.user,
                household=self.household,
                total_points=100
            )

    def test_user_points_str_representation(self):
        """Test user points string representation"""
        points = UserPoints.objects.create(
            user=self.user,
            household=self.household,
            total_points=50
        )
        self.assertIn(self.user.email, str(points))
        self.assertIn(self.household.name, str(points))
        self.assertIn('50', str(points))

    def test_last_updated_is_set(self):
        """Test that last_updated is automatically set"""
        points = UserPoints.objects.create(
            user=self.user,
            household=self.household,
            total_points=50
        )
        self.assertIsNotNone(points.last_updated)
