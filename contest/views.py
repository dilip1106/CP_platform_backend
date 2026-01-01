from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import status

from .models import Contest, ContestProblem, ContestParticipant, ContestRegistration
from .serializers import (
    ContestListSerializer,
    ContestDetailSerializer,
    ContestCreateSerializer,
    ContestDetailWithRegistrationSerializer,
    ContestRegistrationSerializer,
)
from .permissions import (
    IsContestManager,
    CanEditContest,
    CanAddProblems,
    CanPublishContest,
    CanRegisterForContest,
    IsContestParticipant,
    CanSubmitSolution,
    IsContestLive,
)

User = get_user_model()


# ============================================================
# Create Contest (Super Admin Only)
# ============================================================
class ContestCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Create new contest in DRAFT state"""
        serializer = ContestCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Always create in DRAFT state
            contest = serializer.save(
                created_by=request.user,
                state='DRAFT',
                is_published=False
            )
            return Response(
                ContestDetailSerializer(contest, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# List Contests (Public View - Only Published Contests)
# ============================================================
class ContestListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """List published contests (SCHEDULED/LIVE/ENDED/ARCHIVED)"""
        contests = Contest.objects.filter(
            is_published=True
        ).exclude(state='DRAFT').order_by('-created_at')

        serializer = ContestListSerializer(contests, many=True)
        return Response(serializer.data)


# ============================================================
# List Contests with Status
# ============================================================
class ContestListWithStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List contests with their current status"""
        contests = Contest.objects.filter(
            is_published=True
        ).exclude(state='DRAFT').order_by('-created_at')

        data = []
        for contest in contests:
            current_time = now()
            if current_time < contest.start_time:
                status_val = "UPCOMING"
            elif current_time < contest.end_time:
                status_val = "ONGOING"
            else:
                status_val = "ENDED"

            data.append({
                'id': contest.id,
                'title': contest.title,
                'slug': contest.slug,
                'description': contest.description,
                'start_time': contest.start_time,
                'end_time': contest.end_time,
                'status': status_val,
                'is_public': contest.is_public,
                'total_problems': contest.contest_problems.count(),
                'total_participants': contest.participants.count(),
            })

        return Response(data)


# ============================================================
# Search Contests
# ============================================================
class ContestSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Search contests by query"""
        query = request.query_params.get('query', '')
        status_filter = request.query_params.get('status', '')

        contests = Contest.objects.filter(
            is_published=True
        ).exclude(state='DRAFT').order_by('-created_at')

        if query:
            contests = contests.filter(
                title__icontains=query
            ) | contests.filter(
                description__icontains=query
            )

        serializer = ContestListSerializer(contests, many=True)
        return Response(serializer.data)


# ============================================================
# Get Contest Details
# ============================================================
class ContestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        """Get contest details with state-based access"""
        contest = get_object_or_404(Contest, slug=slug)

        is_manager = (
            request.user.is_staff or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )

        if not is_manager and not contest.is_published:
            return Response(
                {"error": "Contest not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ContestDetailSerializer(contest, context={'request': request})
        return Response(serializer.data)


# ============================================================
# Get Contest Details with Registration
# ============================================================
class ContestDetailWithRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        """Get contest details with user registration info"""
        contest = get_object_or_404(Contest, slug=slug)

        is_manager = (
            request.user.is_staff or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )

        if not is_manager and not contest.is_published:
            return Response(
                {"error": "Contest not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ContestDetailWithRegistrationSerializer(
            contest,
            context={'request': request}
        )
        return Response(serializer.data)


# ============================================================
# Get Contest Status (Timing Info)
# ============================================================
class ContestStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        """Get contest status and timing info"""
        contest = get_object_or_404(Contest, slug=slug)
        current_time = now()

        is_manager = (
            request.user.is_staff or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )

        if not is_manager and not contest.is_published:
            return Response(
                {"error": "Contest not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if current_time < contest.start_time:
            status_val = "UPCOMING"
            time_delta = (contest.start_time - current_time).total_seconds()
        elif current_time < contest.end_time:
            status_val = "ONGOING"
            time_delta = (contest.end_time - current_time).total_seconds()
        else:
            status_val = "FINISHED"
            time_delta = 0

        return Response({
            'contest_id': contest.id,
            'title': contest.title,
            'status': status_val,
            'start_time': contest.start_time,
            'end_time': contest.end_time,
            'time_delta_seconds': time_delta,
            'is_joined': ContestParticipant.objects.filter(
                contest=contest,
                user=request.user
            ).exists(),
        })


# ============================================================
# Update Contest (Only in DRAFT/SCHEDULED, Manager Only)
# ============================================================
class ContestUpdateView(APIView):
    permission_classes = [IsAuthenticated, CanEditContest]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def put(self, request, contest_id):
        """Update contest (DRAFT/SCHEDULED only)"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        serializer = ContestCreateSerializer(
            contest,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                ContestDetailSerializer(contest, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, contest_id):
        """Partial update contest"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        serializer = ContestCreateSerializer(
            contest,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                ContestDetailSerializer(contest, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# Publish Contest (Manager Only, Transition DRAFT → SCHEDULED)
# ============================================================
class ContestPublishView(APIView):
    permission_classes = [IsAuthenticated, CanPublishContest]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Publish contest: DRAFT → SCHEDULED"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        if contest.state != 'DRAFT':
            return Response(
                {"error": f"Cannot publish {contest.state} contest"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not ContestProblem.objects.filter(contest=contest).exists():
            return Response(
                {"error": "Contest must have at least one problem"},
                status=status.HTTP_400_BAD_REQUEST
            )

        contest.state = 'SCHEDULED'
        contest.is_published = True
        contest.published_at = now()
        contest.save()

        return Response(
            {
                "message": "Contest published successfully",
                "state": contest.state,
                "is_published": contest.is_published,
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# Add Contest Manager
# ============================================================
class ContestAddManagerView(APIView):
    permission_classes = [IsAdminUser]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Add manager to contest"""
        contest = self.get_contest()

        from .serializers import ContestAddManagerSerializer
        serializer = ContestAddManagerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=serializer.validated_data["user_id"])

        if contest.managers.filter(id=user.id).exists():
            return Response(
                {"error": "User is already a manager"},
                status=status.HTTP_400_BAD_REQUEST
            )

        contest.managers.add(user)

        return Response(
            {"message": "Manager added successfully"},
            status=status.HTTP_200_OK
        )


# ============================================================
# Remove Contest Manager
# ============================================================
class RemoveContestManagerView(APIView):
    permission_classes = [IsAdminUser]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Remove manager from contest"""
        contest = self.get_contest()

        from .serializers import ContestAddManagerSerializer
        serializer = ContestAddManagerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=serializer.validated_data["user_id"])

        if not contest.managers.filter(id=user.id).exists():
            return Response(
                {"error": "User is not a manager"},
                status=status.HTTP_400_BAD_REQUEST
            )

        contest.managers.remove(user)

        return Response(
            {"message": "Manager removed successfully"},
            status=status.HTTP_200_OK
        )


# ============================================================
# Add Problem to Contest
# ============================================================
class ContestAddProblemView(APIView):
    permission_classes = [IsAuthenticated, CanAddProblems]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Add problem to contest"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        from .serializers import ContestAddProblemSerializer
        from problems.models import Problem

        serializer = ContestAddProblemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        problem = get_object_or_404(
            Problem,
            id=serializer.validated_data["problem_id"]
        )

        if ContestProblem.objects.filter(
            contest=contest,
            problem=problem
        ).exists():
            return Response(
                {"error": "Problem already in contest"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ContestProblem.objects.create(
            contest=contest,
            problem=problem,
            order=serializer.validated_data.get("order", 1),
        )

        return Response(
            {"message": "Problem added successfully"},
            status=status.HTTP_201_CREATED
        )


# ============================================================
# Remove Problem from Contest
# ============================================================
class RemoveContestProblemView(APIView):
    permission_classes = [IsAuthenticated, CanAddProblems]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def delete(self, request, contest_id, problem_id):
        """Remove problem from contest"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        contest_problem = get_object_or_404(
            ContestProblem,
            contest=contest,
            problem_id=problem_id
        )

        contest_problem.delete()

        return Response(
            {"message": "Problem removed successfully"},
            status=status.HTTP_200_OK
        )


# ============================================================
# Register for Contest
# ============================================================
class ContestRegisterView(APIView):
    permission_classes = [IsAuthenticated, CanRegisterForContest]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Register for contest"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        if ContestRegistration.objects.filter(
            contest=contest,
            user=request.user,
            status__in=['REGISTERED', 'PARTICIPATED']
        ).exists():
            return Response(
                {"error": "Already registered"},
                status=status.HTTP_400_BAD_REQUEST
            )

        registration = ContestRegistration.objects.create(
            contest=contest,
            user=request.user,
            status='REGISTERED'
        )

        return Response(
            {
                "message": "Successfully registered",
                "registered_at": registration.registered_at,
            },
            status=status.HTTP_201_CREATED
        )


# ============================================================
# Unregister from Contest
# ============================================================
class ContestUnregisterView(APIView):
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Unregister from contest"""
        contest = self.get_contest()

        registration = ContestRegistration.objects.filter(
            contest=contest,
            user=request.user,
            status__in=['REGISTERED', 'PARTICIPATED']
        ).first()

        if not registration:
            return Response(
                {"error": "Not registered for this contest"},
                status=status.HTTP_404_NOT_FOUND
            )

        registration.status = 'CANCELLED'
        registration.save()

        return Response(
            {"message": "Successfully unregistered"},
            status=status.HTTP_200_OK
        )


# ============================================================
# Check Registration Status
# ============================================================
class ContestRegistrationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """Check if user is registered"""
        contest = self.get_contest()

        registration = ContestRegistration.objects.filter(
            contest=contest,
            user=request.user
        ).first()

        if not registration:
            return Response(
                {"registered": False, "status": None},
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "registered": True,
                "status": registration.status,
                "registered_at": registration.registered_at,
                "participated_at": registration.participated_at,
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# List Contest Registrations (Manager Only)
# ============================================================
class ContestRegistrationsListView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """List all registrations for contest"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        registrations = ContestRegistration.objects.filter(
            contest=contest
        ).order_by('-registered_at')

        serializer = ContestRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)


# ============================================================
# User Registered Contests
# ============================================================
class UserRegisteredContestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all contests user is registered for"""
        registrations = ContestRegistration.objects.filter(
            user=request.user,
            status__in=['REGISTERED', 'PARTICIPATED']
        ).order_by('-registered_at')

        data = []
        for reg in registrations:
            contest = reg.contest
            current_time = now()
            if current_time < contest.start_time:
                contest_status = "UPCOMING"
            elif current_time < contest.end_time:
                contest_status = "ONGOING"
            else:
                contest_status = "ENDED"

            data.append({
                'contest_id': contest.id,
                'title': contest.title,
                'slug': contest.slug,
                'description': contest.description,
                'start_time': contest.start_time,
                'end_time': contest.end_time,
                'status': contest_status,
                'registered_at': reg.registered_at,
                'registration_status': reg.status,
            })

        return Response({
            'total_registrations': len(data),
            'contests': data
        })


# ============================================================
# Join Contest (Transition from Registration to Participant)
# ============================================================
class ContestJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Join contest (transition to participant)"""
        contest = self.get_contest()

        if contest.state != 'LIVE':
            return Response(
                {
                    "error": f"Contest is {contest.state}, not LIVE",
                    "contest_state": contest.state
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        registration = ContestRegistration.objects.filter(
            contest=contest,
            user=request.user,
            status__in=['REGISTERED', 'PARTICIPATED']
        ).first()

        if not registration:
            return Response(
                {"error": "Not registered for this contest"},
                status=status.HTTP_403_FORBIDDEN
            )

        participant, created = ContestParticipant.objects.get_or_create(
            contest=contest,
            user=request.user
        )

        registration.status = 'PARTICIPATED'
        registration.participated_at = now()
        registration.save()

        return Response(
            {
                "message": "Joined contest successfully",
                "joined_at": participant.joined_at,
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )


# ============================================================
# Leave Contest
# ============================================================
class ContestLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Leave contest"""
        contest = self.get_contest()

        participant = ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).first()

        if not participant:
            return Response(
                {"error": "Not a participant in this contest"},
                status=status.HTTP_404_NOT_FOUND
            )

        participant.delete()

        return Response(
            {"message": "Successfully left the contest"},
            status=status.HTTP_200_OK
        )


# ============================================================
# Get Contest Problems
# ============================================================
class ContestProblemListView(APIView):
    permission_classes = [IsAuthenticated, IsContestLive, IsContestParticipant]

    def get_contest(self):
        return get_object_or_404(Contest, slug=self.kwargs["slug"])

    def get(self, request, slug):
        """Get contest problems (only LIVE)"""
        contest = self.get_contest()

        problems = ContestProblem.objects.filter(
            contest=contest
        ).order_by("order")

        from .serializers import ContestProblemSerializer
        serializer = ContestProblemSerializer(problems, many=True)
        return Response(serializer.data)


# ============================================================
# Get Contest Problem Details
# ============================================================
class ContestProblemDetailView(APIView):
    permission_classes = [IsAuthenticated, IsContestLive, IsContestParticipant]

    def get_contest(self):
        return get_object_or_404(Contest, slug=self.kwargs["contest_slug"])

    def get(self, request, contest_slug, problem_slug):
        """Get problem details (LIVE only)"""
        contest = self.get_contest()

        from problems.models import Problem
        problem = get_object_or_404(Problem, slug=problem_slug)

        # Verify problem is in contest
        if not ContestProblem.objects.filter(
            contest=contest,
            problem=problem
        ).exists():
            return Response(
                {"error": "Problem not found in contest"},
                status=status.HTTP_404_NOT_FOUND
            )

        from problems.serializers import ProblemDetailSerializer
        serializer = ProblemDetailSerializer(problem)
        return Response(serializer.data)


# ============================================================
# Submit Solution (LIVE State + Time Window Only)
# ============================================================
class ContestSubmissionCreateView(APIView):
    permission_classes = [IsAuthenticated, CanSubmitSolution]

    def get_contest(self):
        return get_object_or_404(
            Contest,
            slug=self.kwargs["contest_slug"]
        )

    def post(self, request, contest_slug, problem_slug):
        """Submit solution to contest"""
        contest = self.get_contest()
        current_time = now()

        if not (contest.start_time <= current_time < contest.end_time):
            time_until = (contest.end_time - current_time).total_seconds()
            return Response(
                {
                    "error": "Submission window closed",
                    "seconds_until_end": max(0, time_until),
                },
                status=status.HTTP_403_FORBIDDEN
            )

        from problems.models import Problem
        from submissions.serializers import SubmissionCreateSerializer

        problem = get_object_or_404(Problem, slug=problem_slug)

        # Verify problem is in contest
        if not ContestProblem.objects.filter(
            contest=contest,
            problem=problem
        ).exists():
            return Response(
                {"error": "Problem not found in contest"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SubmissionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        from submissions.models import Submission
        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            contest=contest,
            language=serializer.validated_data['language'],
            source_code=serializer.validated_data['source_code'],
            status='PENDING'
        )

        from submissions.serializers import SubmissionSerializer
        return Response(
            SubmissionSerializer(submission).data,
            status=status.HTTP_201_CREATED
        )


# ============================================================
# Get User Submissions for Contest Problem
# ============================================================
class UserSubmissionsView(APIView):
    permission_classes = [IsAuthenticated, IsContestLive, IsContestParticipant]

    def get_contest(self):
        return get_object_or_404(Contest, slug=self.kwargs["contest_slug"])

    def get(self, request, contest_slug, problem_slug):
        """Get user submissions for problem"""
        contest = self.get_contest()

        from problems.models import Problem
        from submissions.models import Submission

        problem = get_object_or_404(Problem, slug=problem_slug)

        submissions = Submission.objects.filter(
            user=request.user,
            problem=problem,
            contest=contest
        ).order_by('-created_at')

        from submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


# ============================================================
# Get Submission Details
# ============================================================
class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        """Get submission details"""
        from submissions.models import Submission

        submission = get_object_or_404(Submission, id=submission_id)

        # Only user or manager can view
        is_manager = (
            request.user.is_staff or
            submission.contest.created_by == request.user or
            request.user in submission.contest.managers.all()
        )

        if submission.user != request.user and not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        from submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submission)
        return Response(serializer.data)


# ============================================================
# Get Contest Leaderboard
# ============================================================
class ContestLeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, contest_slug):
        """Get contest leaderboard"""
        contest = get_object_or_404(Contest, slug=contest_slug)

        from submissions.models import Submission
        from django.db.models import Count, Q

        # Get all successful submissions
        submissions = Submission.objects.filter(
            contest=contest,
            status='AC'
        ).select_related('user', 'problem').order_by('user', 'created_at')

        leaderboard = {}
        for sub in submissions:
            if sub.user.username not in leaderboard:
                leaderboard[sub.user.username] = {
                    'user': sub.user.username,
                    'user_id': sub.user.id,
                    'total_score': 0,
                    'problems': []
                }

            problem_data = leaderboard[sub.user.username]['problems']
            if not any(p['problem_id'] == sub.problem.id for p in problem_data):
                leaderboard[sub.user.username]['problems'].append({
                    'problem_id': sub.problem.id,
                    'title': sub.problem.title,
                    'status': 'AC',
                    'solved_at': sub.created_at,
                })
                leaderboard[sub.user.username]['total_score'] += 100

        # Sort by score
        sorted_leaderboard = sorted(
            leaderboard.values(),
            key=lambda x: x['total_score'],
            reverse=True
        )

        return Response(sorted_leaderboard)


# ============================================================
# Get User Contest Stats
# ============================================================
class UserContestStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        """Get user stats for specific contest"""
        contest = get_object_or_404(Contest, slug=slug)

        from submissions.models import Submission

        submissions = Submission.objects.filter(
            user=request.user,
            contest=contest
        )

        total_problems = contest.contest_problems.count()
        problems_solved = submissions.filter(status='AC').values('problem').distinct().count()
        total_attempts = submissions.count()

        data = {
            'user': request.user.username,
            'contest': contest.title,
            'total_problems': total_problems,
            'problems_solved': problems_solved,
            'total_attempts': total_attempts,
            'best_submission_time': submissions.filter(status='AC').first().created_at if submissions.filter(status='AC').exists() else None,
        }

        return Response(data)


# ============================================================
# Manager: View All Contest Submissions
# ============================================================
class ManagerContestSubmissionsView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """View all contest submissions"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        from submissions.models import Submission

        submissions = Submission.objects.filter(
            contest=contest
        ).order_by('-created_at')

        from submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


# ============================================================
# Manager: View Submission Code
# ============================================================
class ManagerViewSubmissionCodeView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id, submission_id):
        """View submission source code"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        from submissions.models import Submission

        submission = get_object_or_404(
            Submission,
            id=submission_id,
            contest=contest
        )

        from submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submission)
        return Response(serializer.data)


# ============================================================
# Manager: Contest Leaderboard
# ============================================================
class ManagerContestLeaderboardView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """View contest leaderboard (manager)"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        from submissions.models import Submission

        submissions = Submission.objects.filter(
            contest=contest,
            status='AC'
        ).select_related('user', 'problem').order_by('user', 'created_at')

        leaderboard = {}
        for sub in submissions:
            if sub.user.username not in leaderboard:
                leaderboard[sub.user.username] = {
                    'user': sub.user.username,
                    'user_id': sub.user.id,
                    'total_score': 0,
                    'problems': []
                }

            problem_data = leaderboard[sub.user.username]['problems']
            if not any(p['problem_id'] == sub.problem.id for p in problem_data):
                leaderboard[sub.user.username]['problems'].append({
                    'problem_id': sub.problem.id,
                    'title': sub.problem.title,
                    'status': 'AC',
                    'submissions_count': Submission.objects.filter(
                        user=sub.user,
                        problem=sub.problem,
                        contest=contest
                    ).count()
                })
                leaderboard[sub.user.username]['total_score'] += 100

        sorted_leaderboard = sorted(
            leaderboard.values(),
            key=lambda x: x['total_score'],
            reverse=True
        )

        return Response({
            'contest_title': contest.title,
            'total_participants': len(sorted_leaderboard),
            'leaderboard': sorted_leaderboard
        })


# ============================================================
# Manager: Submission Analytics
# ============================================================
class ManagerSubmissionAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """Get submission analytics"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        from submissions.models import Submission
        from django.db.models import Count

        submissions = Submission.objects.filter(contest=contest)

        status_dist = submissions.values('status').annotate(count=Count('status'))

        return Response({
            'contest_title': contest.title,
            'total_submissions': submissions.count(),
            'unique_users_submitted': submissions.values('user').distinct().count(),
            'status_distribution': {item['status']: item['count'] for item in status_dist}
        })


# ============================================================
# Manager: Export Contest Data
# ============================================================
class ManagerExportContestDataView(APIView):
    permission_classes = [IsAuthenticated, IsContestManager]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """Export contest data"""
        contest = self.get_contest()
        self.check_object_permissions(request, contest)

        format_type = request.query_params.get('format', 'json')

        from submissions.models import Submission

        submissions = Submission.objects.filter(contest=contest)

        data = []
        for sub in submissions:
            data.append({
                'username': sub.user.username,
                'email': sub.user.email,
                'problem': sub.problem.title,
                'language': sub.language,
                'status': sub.status,
                'created_at': sub.created_at
            })

        if format_type == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['username', 'email', 'problem', 'language', 'status', 'created_at'])
            writer.writeheader()
            writer.writerows(data)
            return Response({
                'format': 'csv',
                'data': output.getvalue()
            })

        return Response({
            'format': 'json',
            'contest_title': contest.title,
            'export_date': now(),
            'data': data
        })


# ============================================================
# Automatic State Transition Service
# ============================================================
class ContestStateTransitionService:
    """
    Service to automatically transition contests based on current time.
    Should be run via Celery periodic task or management command.
    """
    
    @staticmethod
    def update_contest_states():
        """Update contest states based on current time"""
        current_time = now()

        contests_to_go_live = Contest.objects.filter(
            state='SCHEDULED',
            start_time__lte=current_time,
            end_time__gt=current_time
        )
        count_live = contests_to_go_live.update(state='LIVE')

        contests_to_end = Contest.objects.filter(
            state='LIVE',
            end_time__lte=current_time
        )
        count_ended = contests_to_end.update(state='ENDED')

        return {
            "contests_went_live": count_live,
            "contests_ended": count_ended,
        }
