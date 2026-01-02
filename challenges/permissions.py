from rest_framework.permissions import BasePermission
from .models import Challenge, PracticeProblem


class IsManager(BasePermission):
    """
    User is a manager (is_staff or is_superuser).
    Managers can create challenges.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsChallengeCreator(BasePermission):
    """Only challenge creator can edit/delete"""
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or request.user.is_staff


class IsSuperUserOnly(BasePermission):
    """Only superusers can create practice problems"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsPracticeProblemOwnerOrSuperuser(BasePermission):
    """Only superuser can edit/delete practice problems"""
    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser


class IsAuthenticatedOrReadOnly(BasePermission):
    """Allow read-only access to everyone, authenticated for write"""
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return request.user and request.user.is_authenticated


class IsPracticeProblemCreator(BasePermission):
    """Only problem creator (superuser) can edit/delete"""
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or request.user.is_staff
