from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HouseholdViewSet, ChoreViewSet

router = DefaultRouter()
router.register(r'households', HouseholdViewSet, basename='household')
router.register(r'chores', ChoreViewSet, basename='chore')

urlpatterns = [
    path('', include(router.urls)),
]
