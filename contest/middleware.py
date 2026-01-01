"""
Contest State Enforcement Middleware
"""
from django.utils.timezone import now
from .models import Contest

class ContestStateMiddleware:
    """
    Middleware to auto-update contest states on each request.
    Ensures LIVE/ENDED states are current.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update contest states (lightweight, should be cached)
        current_time = now()
        
        # Mark contests that should go live
        Contest.objects.filter(
            state='SCHEDULED',
            start_time__lte=current_time,
            end_time__gt=current_time
        ).update(state='LIVE')

        # Mark contests that should end
        Contest.objects.filter(
            state='LIVE',
            end_time__lte=current_time
        ).update(state='ENDED')

        response = self.get_response(request)
        return response


# EDGE CASE VALIDATORS

class SubmissionValidator:
    """Validate submissions with contest state awareness"""
    
    @staticmethod
    def validate_submission(contest, user, current_time):
        """
        Prevent:
        1. Submissions before contest is LIVE
        2. Submissions after contest ends (grace period?)
        3. Submissions from non-participants
        """
        errors = []

        # Check contest state
        if contest.state != 'LIVE':
            errors.append(f"Contest is {contest.state}, not accepting submissions")

        # Check time window
        if current_time < contest.start_time:
            errors.append("Contest has not started yet")
        if current_time > contest.end_time:
            errors.append("Contest has ended")

        # Check participation
        from .models import ContestParticipant
        if not ContestParticipant.objects.filter(
            contest=contest,
            user=user
        ).exists():
            errors.append("You are not a participant in this contest")

        return {"valid": len(errors) == 0, "errors": errors}


class ContestEditValidator:
    """Prevent edits to LIVE/ENDED contests"""
    
    @staticmethod
    def can_edit_contest(contest):
        """
        Only DRAFT/SCHEDULED can be edited.
        LIVE/ENDED/ARCHIVED are read-only.
        """
        return contest.state in ['DRAFT', 'SCHEDULED']

    @staticmethod
    def can_add_problems(contest):
        """
        Only DRAFT/SCHEDULED can have problems added.
        """
        return contest.state in ['DRAFT', 'SCHEDULED']