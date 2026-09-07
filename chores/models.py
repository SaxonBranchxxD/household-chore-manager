from django.db import models
from django.contrib.auth.models import User


class Household(models.Model):
    """Represents a household/group"""
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_households')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class HouseholdMember(models.Model):
    """Represents a member of a household"""
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='households')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.email} - {self.household.name}'

    class Meta:
        unique_together = ('household', 'user')
        ordering = ['-joined_at']


class Chore(models.Model):
    """Represents a chore"""
    FREQUENCY_CHOICES = (
        ('once', 'One-time'),
        ('weekly', 'Weekly'),
    )

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='chores')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_chores')
    points = models.IntegerField(default=10)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='once')
    due_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_chores')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date']


class ChoreCompletion(models.Model):
    """Tracks when a chore is completed"""
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name='completions')
    completed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_chores')
    completed_at = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField()

    def __str__(self):
        return f'{self.chore.title} - {self.completed_by.email}'

    class Meta:
        ordering = ['-completed_at']


class UserPoints(models.Model):
    """Tracks total points per user per household"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='user_points')
    total_points = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} - {self.household.name}: {self.total_points} pts'

    class Meta:
        unique_together = ('user', 'household')
        ordering = ['-total_points']
