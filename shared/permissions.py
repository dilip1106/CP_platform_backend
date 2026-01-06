from rest_framework.permissions import BasePermission
from django.utils.timezone import now
from django.shortcuts import get_object_or_404


class IsSuperUser(BasePermission):
    """Only superusers allowed"""
    message = "Only superusers can perform this action"
    
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsManager(BasePermission):
    """User must be a manager"""
    message = "Only managers can perform this action"
    
    def has_permission(self, request, view):
        return request.user and request.user.is_manager


class IsManagerOrSuperUser(BasePermission):
    """User is manager or superuser"""
    message = "Only managers or superusers can perform this action"
    
    def has_permission(self, request, view):
        return request.user and (request.user.is_manager or request.user.is_superuser)


class IsSubmissionOwner(BasePermission):
    """Only submission owner can view/delete"""
    message = "You can only view/modify your own submissions"
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsManagerOfContest(BasePermission):
    """
    User is manager of the contest.
    Contest must be available via view.get_contest() or be the object itself.
    """
    message = "You are not a manager of this contest"
    
    def has_permission(self, request, view):
        try:
            if hasattr(view, 'get_contest'):
                contest = view.get_contest()
            else:
                return True
            
            return (
                request.user.is_superuser or
                contest.created_by == request.user or
                request.user in contest.managers.all()
            )
        except:
            return False

    def has_object_permission(self, request, view, obj):
        contest = getattr(obj, 'contest', obj) if hasattr(obj, 'contest') else obj
        
        return (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )


class IsContestLive(BasePermission):
    """Contest must be in LIVE state"""
    message = "Contest is not currently live"
    
    def has_permission(self, request, view):
        try:
            contest = view.get_contest()
            return contest.state == 'LIVE' and contest.is_live()
        except:
            return False


class IsContestParticipant(BasePermission):
    """User must be registered/participated in contest"""
    message = "You are not a participant in this contest"
    
    def has_permission(self, request, view):
        try:
            from contest.models import ContestParticipant
            contest = view.get_contest()
            return ContestParticipant.objects.filter(
                contest=contest,
                user=request.user
            ).exists()
        except:
            return False


class CanViewChallenge(BasePermission):
    """
    Only creator, superuser, or contest participants can view challenge.
    """
    message = "You do not have permission to view this challenge"
    
    def has_object_permission(self, request, view, obj):
        return obj.is_visible_to_user(request.user)


class CanEditChallenge(BasePermission):
    """Only creator and superuser can edit/delete challenges"""
    message = "Only the creator or superuser can edit this challenge"
    
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or request.user.is_superuser


class CanTransitionContestState(BasePermission):
    """User can transition contest to new state"""
    message = "You cannot transition this contest to the requested state"
    
    def has_object_permission(self, request, view, obj):
        new_state = request.data.get('state')
        
        # Only managers can transition
        is_manager = (
            request.user.is_superuser or
            obj.created_by == request.user or
            request.user in obj.managers.all()
        )
        
        if not is_manager:
            return False
        
        # Check if transition is valid
        if new_state and hasattr(obj, 'can_transition_to'):
            return obj.can_transition_to(new_state)
        
        return True


class CanViewSubmissionDetails(BasePermission):
    """Can view source code and testcase details"""
    message = "You cannot view this submission's details"
    
    def has_object_permission(self, request, view, obj):
        submission = obj.submission if hasattr(obj, 'submission') else obj
        
        # Owner always sees
        if submission.user == request.user:
            return True
        
        # Superuser always sees
        if request.user.is_superuser:
            return True
        
        # Manager of contest sees
        if submission.contest:
            return (
                submission.contest.created_by == request.user or
                request.user in submission.contest.managers.all()
            )
        
        return False