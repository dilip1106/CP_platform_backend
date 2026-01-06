from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from .models import Submission, SubmissionResult
from .serializers import (
    SubmissionCreateSerializer,
    SubmissionSerializer,
    SubmissionResultSerializer
)
from shared.permissions import CanViewSubmissionDetails


# ============================================================
# Submission Creation - Practice Problems
# ============================================================

class SubmissionCreateView(APIView):
    """
    Create a new submission for a practice problem.
    
    Accessible to: Authenticated users
    Request body: problem_id, language, source_code
    Returns: Created submission with initial results
    
    Rules:
    - Only for practice problems (not contests)
    - User must be authenticated
    - Validates problem exists and is published
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create submission for practice problem"""
        serializer = SubmissionCreateSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.save(user=request.user)
            return Response(
                SubmissionSerializer(
                    submission,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# List User's Submissions
# ============================================================

class UserSubmissionListView(APIView):
    """
    Get all submissions by the current user.
    
    Accessible to: Authenticated users (own submissions only)
    Returns: List of all submissions (practice + contest)
    Ordered by: Most recent first
    
    Optimizations:
    - select_related: problem, contest, contest_item
    - prefetch_related: results
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve all submissions for current user"""
        # Query optimization: select_related + prefetch_related
        submissions = Submission.objects.filter(
            user=request.user
        ).select_related(
            'problem',
            'contest',
            'contest_item'
        ).prefetch_related('results').order_by('-created_at')
        
        serializer = SubmissionSerializer(
            submissions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# Get Submission Detail
# ============================================================

class SubmissionDetailView(APIView):
    """
    Get submission detail with access control.
    
    Accessible to: 
    - Submission owner
    - Contest manager (if submission is for a contest)
    - Superuser
    
    Returns: Full submission details including:
    - Source code (with access control)
    - All test case results
    - Execution metrics (time, memory)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        """Retrieve submission by ID with access control"""
        submission = get_object_or_404(Submission, id=submission_id)

        # Access control: owner or manager
        is_owner = submission.user == request.user
        is_manager = (
            request.user.is_superuser or
            (submission.contest and (
                submission.contest.created_by == request.user or
                request.user in submission.contest.managers.all()
            ))
        )

        if not is_owner and not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = SubmissionSerializer(
            submission,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# Get Submission Results (Test Cases)
# ============================================================

class SubmissionResultListView(APIView):
    """
    Get all results for a submission.
    
    Accessible to: 
    - Submission owner
    - Contest manager (if submission is for a contest)
    - Superuser
    
    Returns: List of test case results with:
    - Status (AC, WA, TLE, etc.)
    - Execution metrics
    - Input/Output (controlled by can_view_details)
    - stderr output (if available)
    
    Rules:
    - Hidden testcases only visible after contest ends or to owner/manager
    - Sample testcases always visible during contest
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        """Retrieve all results for a submission"""
        submission = get_object_or_404(Submission, id=submission_id)

        # Access control
        is_owner = submission.user == request.user
        is_manager = (
            request.user.is_superuser or
            (submission.contest and (
                submission.contest.created_by == request.user or
                request.user in submission.contest.managers.all()
            ))
        )

        if not is_owner and not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        results = submission.results.all().order_by('id')
        serializer = SubmissionResultSerializer(
            results,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# Get User Submissions for Specific Problem
# ============================================================

class UserProblemSubmissionsView(APIView):
    """
    Get all submissions by user for a specific practice problem.
    
    Accessible to: Authenticated users (own submissions only)
    Returns: List of submissions for the problem
    Ordered by: Most recent first
    
    Rules:
    - Only returns user's own submissions
    - Only for practice problems (not contest submissions)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, problem_id):
        """Get user's submissions for a specific problem"""
        submissions = Submission.objects.filter(
            user=request.user,
            problem_id=problem_id
        ).select_related(
            'problem'
        ).prefetch_related('results').order_by('-created_at')

        if not submissions.exists():
            return Response(
                [],
                status=status.HTTP_200_OK
            )

        serializer = SubmissionSerializer(
            submissions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# Get User Submissions for Specific Contest Problem
# ============================================================

class UserContestProblemSubmissionsView(APIView):
    """
    Get all submissions by user for a specific contest problem.
    
    Accessible to: 
    - Submission owner
    - Contest participant
    - Contest manager
    - Superuser
    
    Returns: List of submissions for the problem in contest
    
    Rules:
    - Filtered by user + contest + problem
    - Only accessible to participants or managers
    - Test case details controlled by can_view_details
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, contest_id, problem_id):
        """Get user's submissions for a contest problem"""
        from contest.models import Contest
        from problems.models import Problem
        
        contest = get_object_or_404(Contest, id=contest_id)
        problem = get_object_or_404(Problem, id=problem_id)

        # Verify user has access
        is_owner = False  # Submissions belong to the user
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )

        if not is_manager and request.user.is_authenticated:
            # Check if participant
            from contest.models import ContestParticipant
            is_participant = ContestParticipant.objects.filter(
                contest=contest,
                user=request.user
            ).exists()
            if not is_participant:
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

        submissions = Submission.objects.filter(
            user=request.user,
            problem=problem,
            contest=contest
        ).select_related(
            'problem',
            'contest'
        ).prefetch_related('results').order_by('-created_at')

        serializer = SubmissionSerializer(
            submissions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# Get Latest Submission for Problem
# ============================================================

class LatestSubmissionView(APIView):
    """
    Get user's latest submission for a problem.
    
    Accessible to: Authenticated users (own submissions only)
    Returns: Latest submission with full details or 404
    
    Useful for: Getting recent verdict/status without listing all
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, problem_id):
        """Get latest submission for a problem"""
        submission = Submission.objects.filter(
            user=request.user,
            problem_id=problem_id
        ).select_related(
            'problem'
        ).prefetch_related('results').order_by('-created_at').first()

        if not submission:
            return Response(
                {"error": "No submissions found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SubmissionSerializer(
            submission,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================
# Get Submission Statistics
# ============================================================

class SubmissionStatsView(APIView):
    """
    Get submission statistics for user.
    
    Accessible to: Authenticated users (own stats only)
    Returns: Aggregated submission metrics:
    - Total submissions
    - Accepted count
    - By language breakdown
    - By status breakdown
    
    Useful for: User dashboard/profile
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get submission statistics for current user"""
        from django.db.models import Count, Q
        
        submissions = Submission.objects.filter(user=request.user)
        
        total = submissions.count()
        accepted = submissions.filter(status='AC').count()
        
        by_language = submissions.values('language').annotate(
            count=Count('language')
        ).order_by('-count')
        
        by_status = submissions.values('status').annotate(
            count=Count('status')
        ).order_by('-count')
        
        stats = {
            'total_submissions': total,
            'accepted_submissions': accepted,
            'acceptance_rate': (accepted / total * 100) if total > 0 else 0,
            'by_language': list(by_language),
            'by_status': list(by_status),
        }
        
        return Response(stats, status=status.HTTP_200_OK)


# ============================================================
# DEPRECATED: SubmitSolutionView
# ============================================================

class SubmitSolutionView(APIView):
    """
    DEPRECATED: Use SubmissionCreateView instead.
    
    This view is maintained for backward compatibility only.
    All new integrations should use SubmissionCreateView.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Deprecated: Submit solution to practice problem.
        Redirects to SubmissionCreateView.
        """
        # Simply delegate to SubmissionCreateView
        view = SubmissionCreateView.as_view()
        return view(request)
