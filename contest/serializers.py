from rest_framework import serializers
from .models import Contest, ContestProblem, ContestParticipant
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
