from rest_framework.permissions import BasePermission
from rest_framework.permissions import BasePermission
from django.utils.timezone import now
from .models import ContestParticipant


class IsContestCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user


class IsContestManager(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            obj.created_by == request.user
            or request.user in obj.managers.all()
        )


class IsContestParticipant(BasePermission):
    """
    Allows access only to users who joined the contest
    and only during contest time.
    """

    def has_permission(self, request, view):
        contest = view.get_contest()

        # Contest time check
        current_time = now()
        if current_time < contest.start_time or current_time > contest.end_time:
            return False

        # Participant check
        return ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).exists()
