from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """User is a manager (is_staff=True)"""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsChallengeCreator(BasePermission):
    """Only challenge creator can edit/delete"""
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or request.user.is_superuser


class IsSuperUserOnly(BasePermission):
    """Only superusers allowed"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class CanViewChallenge(BasePermission):
    """
    Only creator, superuser, or contest participants can view challenge.
    Rules:
    - Creator always sees their challenge
    - Superusers always see all challenges
    - Users see challenges ONLY inside LIVE contests they participate in
    """
    def has_object_permission(self, request, view, obj):
        # Challenge creator or superuser
        if obj.created_by == request.user or request.user.is_superuser:
            return True
        
        # Check if user is accessing challenge inside a contest
        from contest.models import Contest, ContestItem, ContestParticipant
        from django.utils.timezone import now
        
        # Find contests with this challenge that are LIVE
        contest_items = ContestItem.objects.filter(
            challenge=obj,
            contest__state='LIVE'
        )
        
        for item in contest_items:
            if ContestParticipant.objects.filter(
                contest=item.contest,
                user=request.user
            ).exists():
                return True
        
        return False
