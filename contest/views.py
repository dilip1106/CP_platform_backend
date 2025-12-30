from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import status

from .models import Contest, ContestProblem, ContestRegistration
from .serializers import (
    ContestListSerializer,
    ContestDetailSerializer,
    ContestCreateSerializer,
    ContestAddManagerSerializer,
    ContestAddProblemSerializer,
    ContestJoinSerializer,
    ContestRegistrationSerializer,
    ContestDetailWithRegistrationSerializer,
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
from submissions.models import Submission, SubmissionResult
from submissions.serializers import SubmissionCreateSerializer, SubmissionSerializer
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

# ============================================================
# Contest Status View
# ============================================================
class ContestStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug)
        current_time = now()

        if current_time < contest.start_time:
            contest_status = "UPCOMING"
            time_until = (contest.start_time - current_time).total_seconds()
        elif current_time < contest.end_time:
            contest_status = "ONGOING"
            time_until = (contest.end_time - current_time).total_seconds()
        else:
            contest_status = "ENDED"
            time_until = 0

        # Check if user joined
        is_joined = ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).exists()

        return Response({
            "contest_id": contest.id,
            "title": contest.title,
            "status": contest_status,
            "start_time": contest.start_time,
            "end_time": contest.end_time,
            "time_until_event": time_until,
            "is_joined": is_joined,
            "total_participants": contest.participants.count(),
        })


# ============================================================
# Contest Leave View
# ============================================================
class ContestLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contest_id):
        contest = get_object_or_404(Contest, id=contest_id)
        
        participant = ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).first()

        if not participant:
            return Response(
                {"error": "You haven't joined this contest"},
                status=status.HTTP_404_NOT_FOUND
            )

        participant.delete()
        return Response(
            {"message": "Successfully left the contest"},
            status=status.HTTP_200_OK
        )


# ============================================================
# Contest Update View
# ============================================================
class ContestUpdateView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, contest_id):
        contest = get_object_or_404(Contest, id=contest_id)
        serializer = ContestCreateSerializer(contest, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                ContestDetailSerializer(contest).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, contest_id):
        contest = get_object_or_404(Contest, id=contest_id)
        serializer = ContestCreateSerializer(contest, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                ContestDetailSerializer(contest).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# Remove Problem from Contest
# ============================================================
class RemoveContestProblemView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def delete(self, request, contest_id, problem_id):
        contest = get_object_or_404(Contest, id=contest_id)
        self.check_object_permissions(request, contest)

        contest_problem = get_object_or_404(
            ContestProblem,
            contest=contest,
            problem_id=problem_id
        )

        contest_problem.delete()
        return Response(
            {"message": "Problem removed from contest successfully"},
            status=status.HTTP_200_OK
        )


# ============================================================
# Remove Manager from Contest
# ============================================================
class RemoveContestManagerView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, contest_id):
        contest = get_object_or_404(Contest, id=contest_id)
        
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, id=user_id)
        
        if not contest.managers.filter(id=user_id).exists():
            return Response(
                {"error": "User is not a manager of this contest"},
                status=status.HTTP_404_NOT_FOUND
            )

        contest.managers.remove(user)
        return Response(
            {"message": "Manager removed successfully"},
            status=status.HTTP_200_OK
        )


# ============================================================
# User Submission History
# ============================================================
class UserSubmissionsView(APIView):
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

        submissions = Submission.objects.filter(
            user=request.user,
            problem=contest_problem.problem,
            contest=contest
        ).order_by("-created_at")

        from submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


# ============================================================
# Submission Detail View
# ============================================================
class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        submission = get_object_or_404(Submission, id=submission_id)

        # Check permission - user can only view their own submissions
        if submission.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to view this submission"},
                status=status.HTTP_403_FORBIDDEN
            )

        from submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submission)
        return Response(serializer.data)


# ============================================================
# User Contest Statistics
# ============================================================
class UserContestStatsView(APIView):
    permission_classes = [IsAuthenticated, IsContestParticipant]

    def get_contest(self):
        return get_object_or_404(Contest, slug=self.kwargs["slug"])

    def get(self, request, slug):
        contest = self.get_contest()

        # Get all contest problems
        contest_problems = ContestProblem.objects.filter(contest=contest)

        user_stats = {
            "user": request.user.username,
            "contest": contest.title,
            "total_problems": contest_problems.count(),
            "problems_solved": 0,
            "total_attempts": 0,
            "best_submission_time": None,
            "problems": []
        }

        best_time = None

        for cp in contest_problems:
            submissions = Submission.objects.filter(
                user=request.user,
                problem=cp.problem,
                contest=contest
            ).order_by("created_at")

            first_ac = submissions.filter(status="AC").first()
            attempts = submissions.count()
            solved = first_ac is not None

            if solved:
                user_stats["problems_solved"] += 1
                penalty_time = (first_ac.created_at - contest.start_time).total_seconds() / 60
                
                if best_time is None or penalty_time < best_time:
                    best_time = penalty_time
            else:
                penalty_time = None

            user_stats["problems"].append({
                "problem_title": cp.problem.title,
                "problem_slug": cp.problem.slug,
                "solved": solved,
                "attempts": attempts,
                "submission_time": penalty_time,
            })

            user_stats["total_attempts"] += attempts

        if best_time:
            user_stats["best_submission_time"] = best_time

        return Response(user_stats)


# ============================================================
# Search/Filter Contests
# ============================================================
class ContestSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        contests = Contest.objects.filter(is_public=True)

        # Filter by status
        status_filter = request.query_params.get("status")
        if status_filter:
            current_time = now()
            if status_filter.upper() == "UPCOMING":
                contests = contests.filter(start_time__gt=current_time)
            elif status_filter.upper() == "ONGOING":
                contests = contests.filter(
                    start_time__lte=current_time,
                    end_time__gt=current_time
                )
            elif status_filter.upper() == "ENDED":
                contests = contests.filter(end_time__lte=current_time)

        # Filter by difficulty
        difficulty_filter = request.query_params.get("difficulty")
        if difficulty_filter:
            contests = contests.filter(
                contest_problems__problem__difficulty=difficulty_filter
            ).distinct()

        # Filter by title/search
        search_query = request.query_params.get("search")
        if search_query:
            contests = contests.filter(
                title__icontains=search_query
            ) | contests.filter(
                description__icontains=search_query
            )

        # Filter by tags
        tags_filter = request.query_params.get("tags")
        if tags_filter:
            tag_list = tags_filter.split(",")
            contests = contests.filter(
                contest_problems__problem__tags__name__in=tag_list
            ).distinct()

        # Sorting
        sort_by = request.query_params.get("sort_by", "-start_time")
        contests = contests.order_by(sort_by)

        serializer = ContestListSerializer(contests, many=True)
        return Response(serializer.data)


# ============================================================
# Contest List with Status (Enhanced)
# ============================================================
class ContestListWithStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        contests = Contest.objects.filter(is_public=True)
        current_time = now()

        contest_data = []
        for contest in contests:
            if current_time < contest.start_time:
                contest_status = "UPCOMING"
            elif current_time < contest.end_time:
                contest_status = "ONGOING"
            else:
                contest_status = "ENDED"

            contest_serializer = ContestListSerializer(contest)
            contest_dict = contest_serializer.data
            contest_dict["status"] = contest_status
            contest_data.append(contest_dict)

        return Response(contest_data)


# ============================================================
# Register for Contest (Like LeetCode)
# ============================================================
class ContestRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contest_id):
        """User registers for a contest"""
        contest = get_object_or_404(Contest, id=contest_id)

        # Check if contest has started
        if now() >= contest.start_time:
            return Response(
                {"error": "Cannot register - contest has already started"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already registered
        registration = ContestRegistration.objects.filter(
            contest=contest,
            user=request.user
        ).first()

        if registration:
            return Response(
                {"error": f"Already registered - status: {registration.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create registration
        registration = ContestRegistration.objects.create(
            contest=contest,
            user=request.user,
            status='REGISTERED'
        )

        return Response({
            "message": "Successfully registered for contest",
            "contest_id": contest.id,
            "contest_title": contest.title,
            "registered_at": registration.registered_at
        }, status=status.HTTP_201_CREATED)


# ============================================================
# Unregister from Contest
# ============================================================
class ContestUnregisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contest_id):
        """User cancels registration"""
        contest = get_object_or_404(Contest, id=contest_id)

        # Check if contest has started
        if now() >= contest.start_time:
            return Response(
                {"error": "Cannot unregister - contest has already started"},
                status=status.HTTP_400_BAD_REQUEST
            )

        registration = ContestRegistration.objects.filter(
            contest=contest,
            user=request.user,
            status='REGISTERED'
        ).first()

        if not registration:
            return Response(
                {"error": "No active registration found"},
                status=status.HTTP_404_NOT_FOUND
            )

        registration.status = 'CANCELLED'
        registration.save()

        return Response({
            "message": "Successfully unregistered from contest"
        }, status=status.HTTP_200_OK)


# ============================================================
# Get Contest Registrations (Admin/Manager Only)
# ============================================================
class ContestRegistrationsListView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """View all registrations for a contest"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        registrations = ContestRegistration.objects.filter(
            contest=contest
        ).order_by('-registered_at')

        serializer = ContestRegistrationSerializer(registrations, many=True)
        
        return Response({
            "contest_title": contest.title,
            "total_registrations": registrations.count(),
            "active_registrations": registrations.filter(status__in=['REGISTERED', 'PARTICIPATED']).count(),
            "registrations": serializer.data
        })


# ============================================================
# Check Registration Status
# ============================================================
class ContestRegistrationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, contest_id):
        """Check if user is registered for contest"""
        contest = get_object_or_404(Contest, id=contest_id)

        registration = ContestRegistration.objects.filter(
            contest=contest,
            user=request.user
        ).first()

        if not registration:
            return Response({
                "registered": False,
                "status": None,
                "message": "Not registered for this contest"
            })

        current_time = now()
        if current_time < contest.start_time:
            contest_status = "UPCOMING"
        elif current_time < contest.end_time:
            contest_status = "ONGOING"
        else:
            contest_status = "ENDED"

        return Response({
            "registered": True,
            "registration_status": registration.status,
            "registered_at": registration.registered_at,
            "contest_status": contest_status,
            "can_unregister": current_time < contest.start_time
        })


# ============================================================
# Get User's Registered Contests (Dashboard)
# ============================================================
class UserRegisteredContestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all contests user is registered for"""
        registrations = ContestRegistration.objects.filter(
            user=request.user,
            status__in=['REGISTERED', 'PARTICIPATED']
        ).select_related('contest').order_by('-registered_at')

        contests_data = []
        current_time = now()

        for registration in registrations:
            contest = registration.contest

            if current_time < contest.start_time:
                contest_status = "UPCOMING"
            elif current_time < contest.end_time:
                contest_status = "ONGOING"
            else:
                contest_status = "ENDED"

            contests_data.append({
                "contest_id": contest.id,
                "title": contest.title,
                "slug": contest.slug,
                "description": contest.description,
                "start_time": contest.start_time,
                "end_time": contest.end_time,
                "status": contest_status,
                "registered_at": registration.registered_at,
                "registration_status": registration.status,
            })

        return Response({
            "total_registrations": len(contests_data),
            "contests": contests_data
        })


# ============================================================
# Get Contest Detail with Registration Info (Enhanced)
# ============================================================
class ContestDetailWithRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        contest = get_object_or_404(Contest, slug=slug)

        serializer = ContestDetailWithRegistrationSerializer(
            contest,
            context={'request': request}
        )

        return Response(serializer.data)

# ============================================================
# Manager: View All Submissions for a Contest
# ============================================================
class ManagerContestSubmissionsView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """Manager can see all submissions in the contest"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        # Get all submissions for this contest
        submissions = Submission.objects.filter(
            contest=contest
        ).select_related('user', 'problem').order_by('-created_at')

        # Optional filters
        user_id = request.query_params.get('user_id')
        problem_id = request.query_params.get('problem_id')
        status_filter = request.query_params.get('status')  # AC, WA, TLE, etc.

        if user_id:
            submissions = submissions.filter(user_id=user_id)
        if problem_id:
            submissions = submissions.filter(problem_id=problem_id)
        if status_filter:
            submissions = submissions.filter(status=status_filter)

        # Serialize with detailed info
        data = []
        for submission in submissions:
            data.append({
                "id": submission.id,
                "user_id": submission.user.id,
                "username": submission.user.username,
                "problem_id": submission.problem.id,
                "problem_title": submission.problem.title,
                "problem_slug": submission.problem.slug,
                "language": submission.language,
                "status": submission.status,
                "execution_time_ms": submission.execution_time_ms,
                "memory_usage_kb": submission.memory_usage_kb,
                "created_at": submission.created_at,
                "source_code_length": len(submission.source_code),
                "source_code_preview": submission.source_code[:500] + "..." if len(submission.source_code) > 500 else submission.source_code,
            })

        return Response({
            "contest_title": contest.title,
            "total_submissions": len(data),
            "submissions": data
        })


# ============================================================
# Manager: View Specific User's Submission Code
# ============================================================
class ManagerViewSubmissionCodeView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        contest = Contest.objects.filter(
            id=self.kwargs["contest_id"]
        ).first()
        return contest

    def get(self, request, contest_id, submission_id):
        """Manager can view the complete source code of a submission"""
        contest = self.get_contest()
        
        if not contest:
            return Response(
                {"error": "Contest not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify manager permission
        is_manager = (
            contest.created_by == request.user
            or request.user in contest.managers.all()
        )

        if not is_manager and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to view this submission"},
                status=status.HTTP_403_FORBIDDEN
            )

        submission = get_object_or_404(Submission, id=submission_id)

        # Verify submission belongs to this contest
        if submission.contest != contest:
            return Response(
                {"error": "Submission not from this contest"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submission)
        
        return Response({
            **serializer.data,
            "source_code": submission.source_code,  # Full code
            "test_results": [
                {
                    "test_case_id": result.test_case.id,
                    "input": result.test_case.input_data,
                    "expected_output": result.test_case.expected_output,
                    "actual_output": result.stdout,
                    "status": result.status,
                    "execution_time_ms": result.execution_time_ms,
                    "memory_usage_kb": result.memory_usage_kb,
                    "stderr": result.stderr,
                }
                for result in submission.results.all()
            ]
        })


# ============================================================
# Manager: Enhanced Leaderboard with Submission Details
# ============================================================
class ManagerContestLeaderboardView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """Manager sees detailed leaderboard with submission info"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        # Get all participants
        participants = ContestParticipant.objects.filter(
            contest=contest
        ).select_related('user')

        leaderboard = []

        for participant in participants:
            user = participant.user
            user_score = 0
            problem_stats = []

            for cp in ContestProblem.objects.filter(contest=contest):
                # Get all submissions for this problem
                submissions = Submission.objects.filter(
                    user=user,
                    problem=cp.problem,
                    contest=contest
                ).order_by("created_at")

                first_ac = submissions.filter(status="AC").first()
                attempts = submissions.count()
                solved = first_ac is not None

                if solved:
                    user_score += 1
                    penalty_time = (first_ac.created_at - contest.start_time).total_seconds() / 60
                    submission_id = first_ac.id
                else:
                    penalty_time = 0
                    submission_id = None

                problem_stats.append({
                    "problem_id": cp.problem.id,
                    "problem_title": cp.problem.title,
                    "problem_slug": cp.problem.slug,
                    "order": cp.order,
                    "solved": solved,
                    "attempts": attempts,
                    "penalty_time": penalty_time,
                    "ac_submission_id": submission_id,
                    "submission_ids": [s.id for s in submissions],  # All submissions for this problem
                })

            leaderboard.append({
                "rank": 0,  # Will be set after sorting
                "user_id": user.id,
                "username": user.username,
                "user_email": user.email,
                "total_score": user_score,
                "total_penalty_time": sum(p["penalty_time"] for p in problem_stats),
                "problems": problem_stats
            })

        # Sort leaderboard
        leaderboard.sort(
            key=lambda x: (-x["total_score"], x["total_penalty_time"])
        )

        # Assign ranks
        for idx, entry in enumerate(leaderboard, 1):
            entry["rank"] = idx

        return Response({
            "contest_title": contest.title,
            "contest_slug": contest.slug,
            "contest_id": contest.id,
            "total_participants": len(leaderboard),
            "leaderboard": leaderboard
        })


# ============================================================
# Manager: Submission Analytics (Heatmap Data)
# ============================================================
class ManagerSubmissionAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """Get analytics about submissions - useful for contest review"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        submissions = Submission.objects.filter(contest=contest)

        # Count by status
        status_counts = {}
        for choice in Submission.StatusChoices.choices:
            status_code = choice[0]
            status_counts[status_code] = submissions.filter(status=status_code).count()

        # Count by language
        language_counts = {}
        for choice in Submission.LanguageChoices.choices:
            lang_code = choice[0]
            language_counts[lang_code] = submissions.filter(language=lang_code).count()

        # Problems solved count
        problems_solved = {}
        for cp in ContestProblem.objects.filter(contest=contest):
            ac_count = Submission.objects.filter(
                contest=contest,
                problem=cp.problem,
                status="AC"
            ).values('user').distinct().count()
            problems_solved[cp.problem.title] = ac_count

        # Time-based analytics (submissions per hour)
        from django.db.models import Count
        from django.db.models.functions import TruncHour
        
        submissions_by_hour = submissions.annotate(
            hour=TruncHour('created_at')
        ).values('hour').annotate(count=Count('id')).order_by('hour')

        return Response({
            "contest_title": contest.title,
            "total_submissions": submissions.count(),
            "unique_users_submitted": Submission.objects.filter(
                contest=contest
            ).values('user').distinct().count(),
            "status_distribution": status_counts,
            "language_distribution": language_counts,
            "problems_solved_by_count": problems_solved,
            "submissions_timeline": [
                {
                    "hour": item['hour'],
                    "count": item['count']
                }
                for item in submissions_by_hour
            ]
        })


# ============================================================
# Manager: Export Contest Data (CSV/JSON)
# ============================================================
class ManagerExportContestDataView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """Export leaderboard and submissions data"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        export_format = request.query_params.get('format', 'json')  # json or csv

        # Get leaderboard data
        participants = ContestParticipant.objects.filter(
            contest=contest
        ).select_related('user')

        export_data = []

        for participant in participants:
            user = participant.user
            submissions = Submission.objects.filter(
                user=user,
                contest=contest
            )

            ac_count = submissions.filter(status="AC").count()
            wa_count = submissions.filter(status="WA").count()
            tle_count = submissions.filter(status="TLE").count()
            ce_count = submissions.filter(status="CE").count()

            export_data.append({
                "username": user.username,
                "email": user.email,
                "problems_solved": ac_count,
                "wrong_answers": wa_count,
                "time_limit_exceeded": tle_count,
                "compile_errors": ce_count,
                "total_submissions": submissions.count(),
            })

        if export_format.lower() == 'csv':
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'username', 'email', 'problems_solved', 
                'wrong_answers', 'time_limit_exceeded', 
                'compile_errors', 'total_submissions'
            ])
            writer.writeheader()
            writer.writerows(export_data)

            response = Response(output.getvalue(), status=status.HTTP_200_OK)
            response['Content-Type'] = 'text/csv'
            response['Content-Disposition'] = f'attachment; filename="{contest.slug}_leaderboard.csv"'
            return response
        else:
            return Response({
                "contest_title": contest.title,
                "export_date": now(),
                "data": export_data
            })
