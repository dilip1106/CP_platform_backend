from rest_framework.permissions import BasePermission
from django.utils.timezone import now
from .models import Contest, ContestParticipant


class IsContestCreator(BasePermission):
    """Only contest creator can edit"""
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user


class IsContestManager(BasePermission):
    """Creator or assigned manager"""
    def has_object_permission(self, request, view, obj):
        return (
            obj.created_by == request.user
            or request.user in obj.managers.all()
            or request.user.is_staff
        )


class CanEditContest(BasePermission):
    """Can edit only if DRAFT/SCHEDULED"""
    def has_object_permission(self, request, view, obj):
        is_manager = (
            obj.created_by == request.user
            or request.user in obj.managers.all()
            or request.user.is_staff
        )
        return is_manager and obj.state in ['DRAFT', 'SCHEDULED']


class CanAddProblems(BasePermission):
    """Can add problems only in DRAFT/SCHEDULED"""
    def has_object_permission(self, request, view, obj):
        is_manager = (
            obj.created_by == request.user
            or request.user in obj.managers.all()
            or request.user.is_staff
        )
        return is_manager and obj.state in ['DRAFT', 'SCHEDULED']


class IsContestLive(BasePermission):
    """Contest must be in LIVE state"""
    def has_permission(self, request, view):
        contest = view.get_contest()
        return contest.state == 'LIVE'


class CanRegisterForContest(BasePermission):
    """Can register only before contest starts"""
    def has_permission(self, request, view):
        contest = view.get_contest()
        current_time = now()
        
        # Registration allowed before start_time
        if current_time >= contest.start_time:
            return False
        
        # Contest must be published
        return contest.is_published and contest.state in ['SCHEDULED', 'LIVE']


class IsContestParticipant(BasePermission):
    """User must have joined contest AND contest must be LIVE"""
    def has_permission(self, request, view):
        contest = view.get_contest()
        current_time = now()

        # Contest must be LIVE
        if contest.state != 'LIVE':
            return False

        # User must be participant
        return ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).exists()


class CanSubmitSolution(BasePermission):
    """Submissions only during LIVE state"""
    def has_permission(self, request, view):
        contest = view.get_contest()
        current_time = now()

        # Must be LIVE
        if contest.state != 'LIVE':
            return False

        # Must be within contest time window
        if not (contest.start_time <= current_time < contest.end_time):
            return False

        # Must be participant
        return ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).exists()


class CanPublishContest(BasePermission):
    """Publish only DRAFT contests with at least 1 problem"""
    def has_object_permission(self, request, view, obj):
        is_manager = (
            obj.created_by == request.user
            or request.user in obj.managers.all()
            or request.user.is_staff
        )
        
        if not is_manager or obj.state != 'DRAFT':
            return False

        # Must have at least one problem
        from .models import ContestProblem
        has_problems = ContestProblem.objects.filter(
            contest=obj
        ).exists()



        return has_problems
