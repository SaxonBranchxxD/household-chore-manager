from django.contrib import admin
from .models import Household, HouseholdMember, Chore, ChoreCompletion, UserPoints


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__email')


@admin.register(HouseholdMember)
class HouseholdMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'household', 'role', 'joined_at')
    search_fields = ('user__email', 'household__name')
    list_filter = ('role',)


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ('title', 'household', 'assigned_to', 'frequency', 'due_date', 'completed')
    search_fields = ('title', 'household__name')
    list_filter = ('frequency', 'completed', 'created_at')


@admin.register(ChoreCompletion)
class ChoreCompletionAdmin(admin.ModelAdmin):
    list_display = ('chore', 'completed_by', 'points_earned', 'completed_at')
    search_fields = ('chore__title', 'completed_by__email')
    list_filter = ('completed_at',)


@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'household', 'total_points', 'last_updated')
    search_fields = ('user__email', 'household__name')
    list_filter = ('last_updated',)
