from rest_framework import serializers
from django.utils.timezone import now
from .models import Contest, ContestProblem, ContestRegistration,ContestParticipant
from problems.models import Problem


class ContestListSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "slug",
            "start_time",
            "end_time",
            "is_public",
            "created_by",
        ]


class ContestProblemSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source="problem.title", read_only=True)
    problem_slug = serializers.CharField(source="problem.slug", read_only=True)
    difficulty = serializers.CharField(source="problem.difficulty", read_only=True)

    class Meta:
        model = ContestProblem
        fields = [
            "id",
            "order",
            "problem_title",
            "problem_slug",
            "difficulty",
        ]


class ContestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contest
        fields = [
            "title",
            "slug",
            "description",
            "start_time",
            "end_time",
            "is_public",
            "logo",
            "rules",
        ]

    def validate(self, attrs):
        """Validate contest timing"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError(
                    "Start time must be before end time"
                )
            if start_time < now():
                raise serializers.ValidationError(
                    "Start time cannot be in the past"
                )
        return attrs


class ContestDetailSerializer(serializers.ModelSerializer):
    """Enhanced detail serializer with state info"""
    created_by = serializers.StringRelatedField()
    managers = serializers.StringRelatedField(many=True)
    problems = serializers.SerializerMethodField()
    current_state = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_add_problems = serializers.SerializerMethodField()
    time_status = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "rules",
            "logo",
            "start_time",
            "end_time",
            "state",
            "current_state",
            "is_published",
            "created_by",
            "managers",
            "problems",
            "can_edit",
            "can_add_problems",
            "time_status",
        ]

    def get_problems(self, obj):
        """Only return problems if contest is LIVE or user is manager"""
        request = self.context.get('request')
        is_manager = (
            request.user.is_staff or
            obj.created_by == request.user or
            request.user in obj.managers.all()
        )

        # Show problems only if LIVE or manager
        if obj.state == 'LIVE' or is_manager:
            problems = ContestProblem.objects.filter(
                contest=obj
            ).order_by('order')
            return ContestProblemSerializer(problems, many=True).data
        return []

    def get_current_state(self, obj):
        """Get computed state based on current time"""
        current_time = now()
        
        if current_time < obj.start_time:
            return "UPCOMING"
        elif current_time < obj.end_time:
            return "ONGOING"
        else:
            return "FINISHED"

    def get_can_edit(self, obj):
        """Only draft/scheduled contests can be edited"""
        request = self.context.get('request')
        is_manager = (
            request.user.is_staff or
            obj.created_by == request.user or
            request.user in obj.managers.all()
        )
        return is_manager and obj.state in ['DRAFT', 'SCHEDULED']

    def get_can_add_problems(self, obj):
        """Problems can be added only in DRAFT/SCHEDULED"""
        request = self.context.get('request')
        is_manager = (
            request.user.is_staff or
            obj.created_by == request.user or
            request.user in obj.managers.all()
        )
        return is_manager and obj.state in ['DRAFT', 'SCHEDULED']

    def get_time_status(self, obj):
        """Human-readable time status"""
        current_time = now()
        
        if current_time < obj.start_time:
            delta = obj.start_time - current_time
            return {
                "status": "UPCOMING",
                "seconds_until_start": delta.total_seconds()
            }
        elif current_time < obj.end_time:
            delta = obj.end_time - current_time
            return {
                "status": "ONGOING",
                "seconds_until_end": delta.total_seconds()
            }
        else:
            return {
                "status": "FINISHED",
                "ended_at": obj.end_time
            }


class ContestAddManagerSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


class ContestAddProblemSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    order = serializers.IntegerField(min_value=1)


class ContestJoinSerializer(serializers.Serializer):
    """
    Used ONLY for validation + creation
    Contest comes from URL
    """

    def validate(self, attrs):
        request = self.context["request"]
        contest = self.context["contest"]

        if ContestParticipant.objects.filter(
            contest=contest,
            user=request.user
        ).exists():
            raise serializers.ValidationError("Already joined this contest")

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        contest = self.context["contest"]

        return ContestParticipant.objects.create(
            contest=contest,
            user=request.user
        )

class ContestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contest
        fields = [
            "title",
            "slug",
            "description",
            "start_time",
            "end_time",
            "is_public",
        ]

class ContestRegistrationSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ContestRegistration
        fields = [
            'id',
            'user',
            'user_username',
            'user_email',
            'status',
            'registered_at',
            'participated_at',
        ]


class ContestDetailWithRegistrationSerializer(serializers.ModelSerializer):
    """Enhanced detail view with registration info"""
    created_by = serializers.StringRelatedField()
    managers = serializers.StringRelatedField(many=True)
    problems = ContestProblemSerializer(
        source="contest_problems",
        many=True,
        read_only=True,
    )
    registered_count = serializers.SerializerMethodField()
    is_user_registered = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "start_time",
            "end_time",
            "created_by",
            "managers",
            "problems",
            "is_public",
            "registered_count",
            "is_user_registered",
            "can_register",
            "status",
        ]

    def get_registered_count(self, obj):
        return obj.registrations.filter(status__in=['REGISTERED', 'PARTICIPATED']).count()

    def get_is_user_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.registrations.filter(
                user=request.user,
                status__in=['REGISTERED', 'PARTICIPATED']
            ).exists()
        return False

    def get_can_register(self, obj):
        """User can register if contest hasn't started yet"""
        from django.utils.timezone import now
        return now() < obj.start_time

    def get_status(self, obj):
        from django.utils.timezone import now
        current_time = now()
        if current_time < obj.start_time:
            return "UPCOMING"
        elif current_time < obj.end_time:
            return "ONGOING"
        else:
            return "ENDED"