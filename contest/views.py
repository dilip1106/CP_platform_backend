from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import status

from .models import Contest, ContestProblem
from .serializers import (
    ContestListSerializer,
    ContestDetailSerializer,
    ContestCreateSerializer,
    ContestAddManagerSerializer,
    ContestAddProblemSerializer,
    ContestJoinSerializer,
)
from .permissions import IsContestManager
from problems.models import Problem

User = get_user_model()


class ContestListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        contests = Contest.objects.filter(is_public=True)
        serializer = ContestListSerializer(contests, many=True)
        return Response(serializer.data)


class ContestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug)

        if now() < contest.start_time:
            return Response(
                {"error": "Contest has not started yet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ContestDetailSerializer(contest)
        return Response(serializer.data)


class ContestCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ContestCreateSerializer(data=request.data)
        if serializer.is_valid():
            contest = serializer.save(created_by=request.user)
            return Response(
                ContestDetailSerializer(contest).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContestAddManagerView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, contest_id):
        contest = get_object_or_404(Contest, id=contest_id)
        serializer = ContestAddManagerSerializer(data=request.data)

        if serializer.is_valid():
            user = get_object_or_404(
                User,
                id=serializer.validated_data["user_id"]
            )
            contest.managers.add(user)
            return Response({"message": "Manager added successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContestAddProblemView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def post(self, request, contest_id):
        contest = get_object_or_404(Contest, id=contest_id)
        self.check_object_permissions(request, contest)

        serializer = ContestAddProblemSerializer(data=request.data)
        if serializer.is_valid():
            problem = get_object_or_404(
                Problem,
                id=serializer.validated_data["problem_id"],
            )

            ContestProblem.objects.create(
                contest=contest,
                problem=problem,
                order=serializer.validated_data["order"],
            )
            return Response({"message": "Problem added successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContestJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contest_id):
        contest = get_object_or_404(Contest, id=contest_id)

        serializer = ContestJoinSerializer(
            data={},
            context={
                "request": request,
                "contest": contest,
            },
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Successfully joined contest"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.permissions import IsAuthenticated
from .permissions import IsContestParticipant
from .models import ContestProblem
from .serializers import ContestProblemSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response


class ContestProblemListView(APIView):
    permission_classes = [IsAuthenticated, IsContestParticipant]

    def get_contest(self):
        return get_object_or_404(Contest, slug=self.kwargs["slug"])

    def get(self, request, slug):
        contest = self.get_contest()

        problems = ContestProblem.objects.filter(
            contest=contest
        ).order_by("order")

        serializer = ContestProblemSerializer(problems, many=True)
        return Response(serializer.data)

from problems.serializers import ProblemDetailSerializer


class ContestProblemDetailView(APIView):
    permission_classes = [IsAuthenticated, IsContestParticipant]

    def get_contest(self):
        return get_object_or_404(
            Contest,
            slug=self.kwargs["contest_slug"]
        )

    def get(self, request, contest_slug, problem_slug):
        contest = self.get_contest()

        contest_problem = get_object_or_404(
            ContestProblem,
            contest=contest,
            problem__slug=problem_slug
        )

        serializer = ProblemDetailSerializer(contest_problem.problem)
        return Response(serializer.data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
import requests

from contest.models import Contest, ContestProblem
from contest.permissions import IsContestParticipant
from .models import Submission, SubmissionResult
from .serializers import SubmissionCreateSerializer, SubmissionSerializer
from submissions.languages import LANGUAGE_CONFIG

JUDGE0_URL = "https://ce.judge0.com/submissions?base64_encoded=false&wait=true"


class ContestSubmissionCreateView(APIView):
    permission_classes = [IsAuthenticated, IsContestParticipant]

    # Used by IsContestParticipant permission
    def get_contest(self):
        return get_object_or_404(
            Contest,
            slug=self.kwargs["contest_slug"]
        )

    def post(self, request, contest_slug, problem_slug):
        contest = self.get_contest()

        # Ensure problem belongs to this contest
        contest_problem = get_object_or_404(
            ContestProblem,
            contest=contest,
            problem__slug=problem_slug
        )

        problem = contest_problem.problem

        # Create submission
        serializer = SubmissionCreateSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        submission = serializer.save(
            user=request.user,
            problem=problem,
            contest=contest,
            status="PENDING"
        )

        language_id = LANGUAGE_CONFIG.get(submission.language)
        if not language_id:
            submission.status = "ERROR"
            submission.save()
            return Response(
                {"error": "Unsupported language"},
                status=status.HTTP_400_BAD_REQUEST
            )

        test_cases = problem.test_cases.all()
        all_passed = True

        for tc in test_cases:
            payload = {
                "source_code": submission.source_code,
                "language_id": language_id,
                "stdin": tc.input_data,
                "expected_output": tc.expected_output,
                "cpu_time_limit": problem.time_limit_ms / 1000,
                "memory_limit": problem.memory_limit_kb,
            }

            try:
                response = requests.post(JUDGE0_URL, json=payload, timeout=15)
                result = response.json()

                judge_status = result["status"]["description"]
                judge_status_id = result["status"]["id"]

                # Judge0 status mapping
                if judge_status_id == 3:
                    status_code = "AC"
                elif judge_status_id == 6:
                    status_code = "CE"
                    all_passed = False
                elif judge_status_id in [4, 5]:
                    status_code = "TLE"
                    all_passed = False
                else:
                    status_code = "WA"
                    all_passed = False

                SubmissionResult.objects.create(
                    submission=submission,
                    test_case=tc,
                    status=status_code,
                    stdout=result.get("stdout"),
                    stderr=result.get("stderr"),
                    execution_time_ms=int(float(result.get("time", 0)) * 1000),
                    memory_usage_kb=result.get("memory"),
                )

            except Exception as e:
                all_passed = False
                SubmissionResult.objects.create(
                    submission=submission,
                    test_case=tc,
                    status="ERROR",
                    stderr=str(e),
                )

        submission.status = "AC" if all_passed else "WA"
        submission.save()

        return Response(
            SubmissionSerializer(submission).data,
            status=status.HTTP_201_CREATED
        )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Max, Count
from contest.models import Contest, ContestParticipant, ContestProblem
from submissions.models import Submission

class ContestLeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, contest_slug):
        contest = get_object_or_404(Contest, slug=contest_slug)

        # Get all participants
        participants = ContestParticipant.objects.filter(contest=contest)

        leaderboard = []

        for participant in participants:
            user = participant.user
            user_score = 0
            problem_stats = []

            for cp in ContestProblem.objects.filter(contest=contest):
                # Get all submissions for this problem by the participant
                submissions = Submission.objects.filter(
                    user=user,
                    contest=contest,
                    problem=cp.problem
                ).order_by("created_at")

                # Find first AC submission
                first_ac = submissions.filter(status="AC").first()
                attempts = submissions.count()

                if first_ac:
                    user_score += 1  # Full point per problem
                    solved = True
                    penalty_time = (first_ac.created_at - contest.start_time).total_seconds() / 60
                else:
                    solved = False
                    penalty_time = 0

                problem_stats.append({
                    "problem_title": cp.problem.title,
                    "solved": solved,
                    "attempts": attempts,
                    "penalty_time": penalty_time
                })

            leaderboard.append({
                "user": user.username,
                "total_score": user_score,
                "problems": problem_stats
            })

        # Sort leaderboard by total_score descending, then by total penalty_time ascending
        leaderboard.sort(key=lambda x: (-x["total_score"], sum(p["penalty_time"] for p in x["problems"])))

        return Response(leaderboard)
