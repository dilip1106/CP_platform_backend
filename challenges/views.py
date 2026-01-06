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
from contest.models import Contest


# ============================================================
# MANAGER CHALLENGE APIS
# ============================================================

class ChallengeCreateView(APIView):
    """Create a new challenge"""
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


class ChallengeListView(APIView):
    """List all challenges created by user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        challenges = Challenge.objects.filter(created_by=request.user)
        serializer = ChallengeListSerializer(challenges, many=True)
        return Response(serializer.data)


class ChallengeDetailView(APIView):
    """Get, update, or delete a challenge"""
    permission_classes = [IsAuthenticated, IsChallengeCreator]

    def get_challenge(self):
        return get_object_or_404(Challenge, id=self.kwargs["challenge_id"])

    def get(self, request, challenge_id):
        challenge = self.get_challenge()
        serializer = ChallengeDetailSerializer(challenge)
        return Response(serializer.data)

    def put(self, request, challenge_id):
        challenge = self.get_challenge()
        self.check_object_permissions(request, challenge)

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
        self.check_object_permissions(request, challenge)

        challenge.delete()
        return Response(
            {"message": "Challenge deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


class ChallengeTestCaseCreateView(APIView):
    """Add test case to challenge"""
    permission_classes = [IsAuthenticated, IsChallengeCreator]

    def get_challenge(self):
        return get_object_or_404(Challenge, id=self.kwargs["challenge_id"])

    def post(self, request, challenge_id):
        challenge = self.get_challenge()
        self.check_object_permissions(request, challenge)

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
# (Auto-visible after contest ends)
# ============================================================
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from challenges.models import Challenge
from contest.models import ContestItem
from .serializers import ChallengeListSerializer, ChallengeDetailSerializer


class PublicPracticeChallengesView(APIView):
    """
    List challenges available for public practice.
    Only shows challenges where:
    - allow_public_practice_after_contest = true
    - Associated contest state = ENDED
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all challenges marked for public practice
        challenges = Challenge.objects.filter(
            allow_public_practice_after_contest=True
        )

        # Filter by challenges that are in any ENDED contest
        from django.utils.timezone import now
        ended_contest_item_ids = ContestItem.objects.filter(
            challenge__in=challenges,
            contest__state='ENDED'
        ).values_list('challenge_id', flat=True).distinct()

        challenges = challenges.filter(id__in=ended_contest_item_ids)

        serializer = ChallengeListSerializer(challenges, many=True)
        return Response(serializer.data)


class PublicPracticeChallengeDetailView(APIView):
    """Get public practice challenge details"""
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

        serializer = ChallengeDetailSerializer(challenge)
        return Response(serializer.data)

# ============================================================
# SUPERUSER PRACTICE PROBLEM APIS
# ============================================================

class PracticeProblemCreateView(APIView):
    """Create a new practice problem (superuser only)"""
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
    """List all public practice problems"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        problems = PracticeProblem.objects.all()
        serializer = PracticeProblemListSerializer(problems, many=True)
        return Response(serializer.data)


class PracticeProblemDetailView(APIView):
    """Get, update, or delete a practice problem"""
    permission_classes = [IsAuthenticated]

    def get_problem(self):
        return get_object_or_404(PracticeProblem, id=self.kwargs["problem_id"])

    def get(self, request, problem_id):
        problem = self.get_problem()
        serializer = PracticeProblemDetailSerializer(problem)
        return Response(serializer.data)

    def put(self, request, problem_id):
        problem = self.get_problem()

        # Check permission
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

        # Check permission
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
    """Add test case to practice problem"""
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
