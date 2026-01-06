from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status

from .models import Challenge, ChallengeTestCase, PracticeProblem, PracticeProblemTestCase
from .serializers import (
    ChallengeListSerializer,
    ChallengeDetailSerializer,
    ChallengeCreateUpdateSerializer,
    PracticeProblemListSerializer,
    PracticeProblemDetailSerializer,
    PracticeProblemCreateUpdateSerializer,
)
from .permissions import IsChallengeCreator, IsSuperUserOnly
from contest.models import ContestItem, ContestParticipant


# ============================================================
# MANAGER CHALLENGE APIS
# ============================================================

class ChallengeCreateView(APIView):
    """
    Create a new challenge.
    
    Accessible to: Managers only (is_staff=True or is_superuser)
    Request body: title, slug, statement, input_format, output_format, 
                  difficulty, time_limit, memory_limit, tags
    Returns: Created challenge details
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = ChallengeCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            challenge = serializer.save(created_by=request.user)
            return Response(
                ChallengeDetailSerializer(challenge).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChallengeListMyView(APIView):
    """
    List all challenges created by the current user.
    
    Accessible to: Authenticated managers
    Returns: List of user's challenges (minimal info)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        challenges = Challenge.objects.filter(
            created_by=request.user
        ).order_by('-created_at')
        
        serializer = ChallengeListSerializer(challenges, many=True)
        return Response(serializer.data)


class ChallengeDetailView(APIView):
    """
    Get, update, or delete a challenge.
    
    GET: Accessible to challenge creator or superuser
    PUT: Update challenge (only creator or superuser)
    DELETE: Delete challenge (only creator or superuser)
    """
    permission_classes = [IsAuthenticated, IsChallengeCreator]

    def get_challenge(self):
        return get_object_or_404(Challenge, id=self.kwargs["challenge_id"])

    def get(self, request, challenge_id):
        challenge = self.get_challenge()
        
        # Verify access
        if challenge.created_by != request.user and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ChallengeDetailSerializer(challenge)
        return Response(serializer.data)

    def put(self, request, challenge_id):
        challenge = self.get_challenge()
        
        # Verify access
        if challenge.created_by != request.user and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ChallengeCreateUpdateSerializer(
            challenge,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                ChallengeDetailSerializer(challenge).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, challenge_id):
        challenge = self.get_challenge()
        
        # Verify access
        if challenge.created_by != request.user and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        challenge.delete()
        return Response(
            {"message": "Challenge deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


class ChallengeTestCaseCreateView(APIView):
    """
    Add test case to a challenge.
    
    Accessible to: Challenge creator or superuser
    Request body: input_data, expected_output, is_sample, is_hidden
    Returns: Created test case details
    """
    permission_classes = [IsAuthenticated]

    def get_challenge(self):
        return get_object_or_404(Challenge, id=self.kwargs["challenge_id"])

    def post(self, request, challenge_id):
        challenge = self.get_challenge()

        # Verify ownership
        if challenge.created_by != request.user and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        test_case = ChallengeTestCase.objects.create(
            challenge=challenge,
            input_data=request.data.get('input_data', ''),
            expected_output=request.data.get('expected_output', ''),
            is_sample=request.data.get('is_sample', False),
            is_hidden=request.data.get('is_hidden', False),
        )

        return Response(
            {
                'id': test_case.id,
                'input_data': test_case.input_data,
                'expected_output': test_case.expected_output,
                'is_sample': test_case.is_sample,
                'is_hidden': test_case.is_hidden,
            },
            status=status.HTTP_201_CREATED
        )


# ============================================================
# PUBLIC PRACTICE CHALLENGES
# ============================================================

class PublicPracticeChallengesView(APIView):
    """
    List challenges available for public practice.
    
    Accessible to: Authenticated users
    Rules: Only challenges where:
           - allow_public_practice_after_contest = true
           - Associated contest state = ENDED
    Returns: List of publicly available challenges
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all challenges marked for public practice
        challenges = Challenge.objects.filter(
            allow_public_practice_after_contest=True,
            state='PUBLISHED'
        )

        # Filter by challenges that are in any ENDED contest
        ended_contest_item_ids = ContestItem.objects.filter(
            challenge__in=challenges,
            contest__state='ENDED'
        ).values_list('challenge_id', flat=True).distinct()

        challenges = challenges.filter(id__in=ended_contest_item_ids)

        serializer = ChallengeListSerializer(challenges, many=True)
        return Response(serializer.data)


class PublicPracticeChallengeDetailView(APIView):
    """
    Get public practice challenge details.
    
    Accessible to: Authenticated users
    Rules: Challenge must be marked for public practice AND
           associated contest must be ENDED
    Returns: Challenge detail with sample test cases
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        challenge = get_object_or_404(Challenge, slug=slug)

        # Verify it's marked for public practice
        if not challenge.allow_public_practice_after_contest:
            return Response(
                {"error": "Challenge not available for practice"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify associated contest is ENDED
        is_in_ended_contest = ContestItem.objects.filter(
            challenge=challenge,
            contest__state='ENDED'
        ).exists()

        if not is_in_ended_contest:
            return Response(
                {"error": "Challenge not yet available"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ChallengeDetailSerializer(
            challenge,
            context={'request': request}
        )
        return Response(serializer.data)


# ============================================================
# SUPERUSER PRACTICE PROBLEM APIS
# ============================================================

class PracticeProblemCreateView(APIView):
    """
    Create a new practice problem.
    
    Accessible to: Superusers only
    Request body: title, slug, statement, input_format, output_format,
                  difficulty, time_limit, memory_limit, tags
    Returns: Created practice problem details
    """
    permission_classes = [IsAuthenticated, IsSuperUserOnly]

    def post(self, request):
        serializer = PracticeProblemCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            problem = serializer.save(created_by=request.user)
            return Response(
                PracticeProblemDetailSerializer(problem).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PracticeProblemListView(APIView):
    """
    List all public practice problems.
    
    Accessible to: Authenticated users
    Returns: List of practice problems (minimal info)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        problems = PracticeProblem.objects.all().order_by('-created_at')
        serializer = PracticeProblemListSerializer(problems, many=True)
        return Response(serializer.data)


class PracticeProblemDetailView(APIView):
    """
    Get, update, or delete a practice problem.
    
    GET: Accessible to all authenticated users
    PUT: Update practice problem (only creator or superuser)
    DELETE: Delete practice problem (only creator or superuser)
    """
    permission_classes = [IsAuthenticated]

    def get_problem(self):
        return get_object_or_404(PracticeProblem, id=self.kwargs["problem_id"])

    def get(self, request, problem_id):
        problem = self.get_problem()
        serializer = PracticeProblemDetailSerializer(
            problem,
            context={'request': request}
        )
        return Response(serializer.data)

    def put(self, request, problem_id):
        problem = self.get_problem()

        # Check permission: only creator or superuser
        if problem.created_by != request.user and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PracticeProblemCreateUpdateSerializer(
            problem,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                PracticeProblemDetailSerializer(problem).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, problem_id):
        problem = self.get_problem()

        # Check permission: only creator or superuser
        if problem.created_by != request.user and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        problem.delete()
        return Response(
            {"message": "Problem deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


class PracticeProblemTestCaseCreateView(APIView):
    """
    Add test case to a practice problem.
    
    Accessible to: Superusers only
    Request body: input_data, expected_output, is_sample
    Returns: Created test case details
    """
    permission_classes = [IsAuthenticated, IsSuperUserOnly]

    def get_problem(self):
        return get_object_or_404(PracticeProblem, id=self.kwargs["problem_id"])

    def post(self, request, problem_id):
        problem = self.get_problem()

        test_case = PracticeProblemTestCase.objects.create(
            problem=problem,
            input_data=request.data.get('input_data', ''),
            expected_output=request.data.get('expected_output', ''),
            is_sample=request.data.get('is_sample', False),
        )

        return Response(
            {
                'id': test_case.id,
                'input_data': test_case.input_data,
                'expected_output': test_case.expected_output,
                'is_sample': test_case.is_sample,
            },
            status=status.HTTP_201_CREATED
        )
