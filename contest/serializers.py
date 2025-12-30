from rest_framework import serializers
from .models import Contest, ContestProblem, ContestParticipant, ContestRegistration
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


class ContestDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    managers = serializers.StringRelatedField(many=True)
    problems = ContestProblemSerializer(
        source="contest_problems",
        many=True,
        read_only=True,
    )

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
        ]


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