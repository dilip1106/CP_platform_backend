from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Submission, SubmissionResult
from .serializers import (
    SubmissionCreateSerializer,
    SubmissionSerializer,
    SubmissionResultSerializer
)


# ============================================================
# Submission Views
# ============================================================

class SubmissionCreateView(APIView):
    """
    Create a new submission for a problem or practice problem.
    
    Accessible to: Authenticated users
    Request body: problem_id or practice_problem_id, language, source_code
    Returns: Created submission with initial results
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
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


class UserSubmissionListView(APIView):
    """
    Get all submissions by the current user.
    
    Accessible to: Authenticated users (own submissions only)
    Returns: List of submissions with optimized queries
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Query optimization: select_related + prefetch_related
        submissions = Submission.objects.filter(
            user=request.user
        ).select_related(
            'problem',
            'contest'
        ).prefetch_related('results').order_by('-created_at')
        
        serializer = SubmissionSerializer(
            submissions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class SubmissionDetailView(APIView):
    """
    Get submission detail with access control.
    
    Accessible to: 
    - Submission owner
    - Contest manager (if submission is for a contest)
    - Superuser
    
    Returns: Full submission details including source code and results
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
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
        return Response(serializer.data)


class SubmissionResultListView(APIView):
    """
    Get all results for a submission.
    
    Accessible to: 
    - Submission owner
    - Contest manager (if submission is for a contest)
    - Superuser
    
    Returns: List of test case results with detailed status info
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
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
        serializer = SubmissionResultSerializer(results, many=True)
        return Response(serializer.data)


class UserProblemSubmissionsView(APIView):
    """
    Get all submissions by user for a specific problem.
    
    Accessible to: Authenticated users (own submissions only)
    Returns: List of submissions for the problem, ordered by creation date
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, problem_id):
        submissions = Submission.objects.filter(
            user=request.user,
            problem_id=problem_id
        ).select_related('problem').prefetch_related('results').order_by('-created_at')

        serializer = SubmissionSerializer(
            submissions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
