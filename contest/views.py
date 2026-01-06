from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, BasePermission
from rest_framework import status
import csv
import io

from .models import Contest, ContestItem, ContestParticipant, ContestRegistration
from .serializers import (
    ContestListSerializer,
    ContestDetailSerializer,
    ContestCreateSerializer,
    ContestAddItemSerializer,
    ContestAddManagerSerializer,
    ContestDetailWithRegistrationSerializer,
    ContestRegistrationSerializer,
    ContestItemSerializer,
)
from shared.permissions import (
    IsManager,
    IsManagerOrSuperUser,
    IsManagerOfContest,
    IsContestLive,
    IsContestParticipant,
)

User = get_user_model()


# ============================================================
# Permission Classes (Local Definitions)
# ============================================================
class CanEditContest(IsManagerOfContest):
    """Only managers can edit DRAFT/SCHEDULED contests"""
    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):
            return False
        return obj.state in ['DRAFT', 'SCHEDULED']


class CanPublishContest(IsManagerOfContest):
    """Only managers can publish DRAFT contests"""
    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):
            return False
        return obj.state == 'DRAFT'


class CanRegisterForContest(BasePermission):
    """User can register before contest starts"""
    def has_object_permission(self, request, view, obj):
        return now() < obj.start_time


class CanSubmitSolution(BasePermission):
    """User can submit during contest window"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsContestManager(IsManagerOfContest):
    """Manager of the contest"""
    pass


# ============================================================
# Create Contest (Super Admin Only)
# ============================================================
class ContestCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Create new contest in DRAFT state"""
        serializer = ContestCreateSerializer(data=request.data)
        if serializer.is_valid():
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
                'total_items': contest.contest_items.count(),
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
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def put(self, request, contest_id):
        """Update contest (DRAFT/SCHEDULED only)"""
        contest = self.get_contest()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager or contest.state not in ['DRAFT', 'SCHEDULED']:
            return Response(
                {"error": "Cannot update this contest"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ContestCreateSerializer(
            contest,
            data=request.data,
            partial=False
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
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager or contest.state not in ['DRAFT', 'SCHEDULED']:
            return Response(
                {"error": "Cannot update this contest"},
                status=status.HTTP_403_FORBIDDEN
            )

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
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Publish contest: DRAFT → SCHEDULED"""
        contest = self.get_contest()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        if contest.state != 'DRAFT':
            return Response(
                {"error": f"Cannot publish {contest.state} contest"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # FIXED: Changed from ContestProblem to ContestItem
        if not ContestItem.objects.filter(contest=contest).exists():
            return Response(
                {"error": "Contest must have at least one item"},
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
# Add Contest Item (Problem or Challenge) - Unified Endpoint
# ============================================================
class ContestAddItemView(APIView):
    """Add problem or challenge to contest (unified endpoint)"""
    permission_classes = [IsAuthenticated, IsManagerOrSuperUser]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Add problem or challenge to contest"""
        contest = self.get_contest()
        
        # Check manager permission
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if contest.state not in ['DRAFT', 'SCHEDULED']:
            return Response(
                {"error": f"Cannot add items to {contest.state} contest"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ContestAddItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        item_type = serializer.validated_data['item_type']
        item_id = serializer.validated_data['item_id']
        order = serializer.validated_data['order']
        score = serializer.validated_data.get('score', 100)

        # Validate and get the item
        if item_type == 'PROBLEM':
            from problems.models import Problem
            try:
                item = Problem.objects.get(id=item_id)
            except Problem.DoesNotExist:
                return Response(
                    {"error": "Problem not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:  # CHALLENGE
            from challenges.models import Challenge
            try:
                item = Challenge.objects.get(id=item_id)
            except Challenge.DoesNotExist:
                return Response(
                    {"error": "Challenge not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Challenge creator must be manager of contest or superuser
            if item.created_by != request.user and not request.user.is_superuser:
                return Response(
                    {"error": "You can only add your own challenges"},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Check if already added
        existing = ContestItem.objects.filter(
            contest=contest,
            item_type=item_type
        ).filter(
            problem=item if item_type == 'PROBLEM' else None,
            challenge=item if item_type == 'CHALLENGE' else None
        ).exists()

        if existing:
            return Response(
                {"error": f"{item_type} already in contest"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create ContestItem
        try:
            contest_item = ContestItem.objects.create(
                contest=contest,
                problem=item if item_type == 'PROBLEM' else None,
                challenge=item if item_type == 'CHALLENGE' else None,
                item_type=item_type,
                order=order,
                score=score
            )
            
            return Response(
                {
                    "message": f"{item_type} added successfully",
                    "contest_item": ContestItemSerializer(contest_item).data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to add item: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


# Keep for backward compatibility - redirect to ContestAddItemView
class ContestAddProblemView(APIView):
    """DEPRECATED: Use ContestAddItemView instead"""
    permission_classes = [IsAuthenticated, IsManagerOrSuperUser]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Add problem to contest (DEPRECATED)"""
        # Convert to new unified format
        if hasattr(request.data, '_mutable'):
            request.data._mutable = True
        request.data['item_type'] = 'PROBLEM'
        if 'problem_id' in request.data:
            request.data['item_id'] = request.data.pop('problem_id')
        
        # Call unified endpoint
        view = ContestAddItemView.as_view()
        return view(request, contest_id=contest_id)


# ============================================================
# Remove Contest Item (Problem or Challenge)
# ============================================================
class RemoveContestItemView(APIView):
    """Remove problem or challenge from contest"""
    permission_classes = [IsAuthenticated, IsManagerOrSuperUser]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def delete(self, request, contest_id, item_id):
        """Remove item from contest"""
        contest = self.get_contest()
        
        # Check manager permission
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            contest_item = ContestItem.objects.get(id=item_id, contest=contest)
        except ContestItem.DoesNotExist:
            return Response(
                {"error": "Item not found in contest"},
                status=status.HTTP_404_NOT_FOUND
            )

        item_type = contest_item.item_type
        item_title = contest_item.get_item().title
        
        contest_item.delete()

        return Response(
            {
                "message": f"{item_type} removed successfully",
                "removed_item": {
                    "type": item_type,
                    "title": item_title,
                    "id": item_id
                }
            },
            status=status.HTTP_200_OK
        )


# Keep for backward compatibility - redirect to RemoveContestItemView
class RemoveContestProblemView(APIView):
    """DEPRECATED: Use RemoveContestItemView instead"""
    permission_classes = [IsAuthenticated, IsManagerOrSuperUser]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def delete(self, request, contest_id, problem_id):
        """Remove problem from contest (DEPRECATED)"""
        try:
            contest = self.get_contest()
            contest_item = ContestItem.objects.get(
                contest=contest,
                problem_id=problem_id
            )
            
            # Call unified endpoint
            view = RemoveContestItemView.as_view()
            return view(request, contest_id=contest_id, item_id=contest_item.id)
        except ContestItem.DoesNotExist:
            return Response(
                {"error": "Problem not found in contest"},
                status=status.HTTP_404_NOT_FOUND
            )


# ============================================================
# Register for Contest
# ============================================================
class ContestRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def post(self, request, contest_id):
        """Register for contest"""
        contest = self.get_contest()

        if now() >= contest.start_time:
            return Response(
                {"error": "Contest has already started"},
                status=status.HTTP_400_BAD_REQUEST
            )

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
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """List all registrations for contest"""
        contest = self.get_contest()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

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
# Get Contest Items (Problems + Challenges)
# ============================================================
class ContestProblemListView(APIView):
    """Get contest items (problems + challenges)"""
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, slug=self.kwargs["slug"])

    def get(self, request, slug):
        """Get contest items"""
        contest = self.get_contest()
        
        # Check if user is participant or manager
        is_participant = ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).exists()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not (is_participant or is_manager) or contest.state != 'LIVE':
            return Response(
                {"error": "Cannot access contest items"},
                status=status.HTTP_403_FORBIDDEN
            )

        items = contest.contest_items.all().order_by("order")
        
        serializer = ContestItemSerializer(items, many=True)
        return Response(serializer.data)


# ============================================================
# Get Contest Item Details (Replaces ContestProblemDetailView)
# ============================================================
class ContestItemDetailView(APIView):
    """Get problem or challenge detail from contest"""
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, slug=self.kwargs["contest_slug"])

    def get(self, request, contest_slug, item_slug):
        """Get item (problem/challenge) details"""
        contest = self.get_contest()
        
        # Check if user is participant or manager
        is_participant = ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).exists()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not (is_participant or is_manager) or contest.state != 'LIVE':
            return Response(
                {"error": "Cannot access contest items"},
                status=status.HTTP_403_FORBIDDEN
            )

        from problems.models import Problem
        from challenges.models import Challenge
        
        # Try problem first
        try:
            problem = Problem.objects.get(slug=item_slug)
            if ContestItem.objects.filter(
                contest=contest,
                problem=problem
            ).exists():
                from problems.serializers import ProblemDetailSerializer
                serializer = ProblemDetailSerializer(
                    problem,
                    context={'request': request}
                )
                return Response(serializer.data)
        except Problem.DoesNotExist:
            pass

        # Try challenge
        try:
            challenge = Challenge.objects.get(slug=item_slug)
            if ContestItem.objects.filter(
                contest=contest,
                challenge=challenge
            ).exists():
                from challenges.serializers import ChallengeDetailSerializer
                serializer = ChallengeDetailSerializer(
                    challenge,
                    context={'request': request}
                )
                return Response(serializer.data)
        except Challenge.DoesNotExist:
            pass

        return Response(
            {"error": "Item not found in contest"},
            status=status.HTTP_404_NOT_FOUND
        )


# Keep for backward compatibility - redirect to ContestItemDetailView
class ContestProblemDetailView(ContestItemDetailView):
    """DEPRECATED: Use ContestItemDetailView instead"""
    pass


# ============================================================
# Submit Solution (LIVE State + Time Window Only)
# ============================================================
class ContestSubmissionCreateView(APIView):
    permission_classes = [IsAuthenticated]

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

        # Verify problem is in contest using ContestItem
        if not ContestItem.objects.filter(
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
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, slug=self.kwargs["contest_slug"])

    def get(self, request, contest_slug, problem_slug):
        """Get user submissions for problem"""
        contest = self.get_contest()
        
        # Check if user is participant or manager
        is_participant = ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).exists()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not (is_participant or is_manager):
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

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
            (submission.contest and (
                submission.contest.created_by == request.user or
                request.user in submission.contest.managers.all()
            ))
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

        total_items = contest.contest_items.count()
        problems_solved = submissions.filter(status='AC').values('problem').distinct().count()
        total_attempts = submissions.count()

        data = {
            'user': request.user.username,
            'contest': contest.title,
            'total_items': total_items,
            'problems_solved': problems_solved,
            'total_attempts': total_attempts,
            'best_submission_time': submissions.filter(status='AC').first().created_at if submissions.filter(status='AC').exists() else None,
        }

        return Response(data)


# ============================================================
# Manager: View All Contest Submissions
# ============================================================
class ManagerContestSubmissionsView(APIView):
    """
    Manager endpoint to view all contest submissions.
    
    Rules:
    - Only contest manager can access
    - Returns user + code + verdict + failed testcases
    """
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """View all contest submissions"""
        contest = self.get_contest()
        
        # Verify manager permission
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        from submissions.models import Submission
        from submissions.serializers import SubmissionSerializer

        # Get all submissions with optimization
        submissions = Submission.objects.filter(
            contest=contest
        ).select_related(
            'user',
            'problem',
            'contest_item',
            'contest_item__problem',
            'contest_item__challenge'
        ).prefetch_related('results').order_by('-created_at')

        serializer = SubmissionSerializer(
            submissions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


# ============================================================
# Manager: View Submission Code
# ============================================================
class ManagerViewSubmissionCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id, submission_id):
        """View submission source code"""
        contest = self.get_contest()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        from submissions.models import Submission

        submission = get_object_or_404(
            Submission,
            id=submission_id,
            contest=contest
        )

        from submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submission, context={'request': request})
        return Response(serializer.data)


# ============================================================
# Manager: Contest Leaderboard
# ============================================================
class ManagerContestLeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """View contest leaderboard (manager)"""
        contest = self.get_contest()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

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
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """Get submission analytics"""
        contest = self.get_contest()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

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
    permission_classes = [IsAuthenticated]

    def get_contest(self):
        return get_object_or_404(Contest, id=self.kwargs["contest_id"])

    def get(self, request, contest_id):
        """Export contest data"""
        contest = self.get_contest()
        
        is_manager = (
            request.user.is_superuser or
            contest.created_by == request.user or
            request.user in contest.managers.all()
        )
        
        if not is_manager:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        format_type = request.query_params.get('format', 'json')

        from submissions.models import Submission

        submissions = Submission.objects.filter(contest=contest)

        data = []
        for sub in submissions:
            data.append({
                'username': sub.user.username,
                'email': sub.user.email,
                'problem': sub.problem.title if sub.problem else 'N/A',
                'language': sub.language,
                'status': sub.status,
                'created_at': sub.created_at
            })

        if format_type == 'csv':
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
