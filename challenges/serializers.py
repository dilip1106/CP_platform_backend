from rest_framework import serializers
from django.utils.timezone import now
from .models import Challenge, ChallengeTestCase, PracticeProblem, PracticeProblemTestCase


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = serializers.Serializer._declared_fields.get('tags', serializers.ModelSerializer)
        fields = ['id', 'name']


class SampleChallengeTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeTestCase
        fields = ['input_data', 'expected_output']


class ChallengeListSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()

    class Meta:
        model = Challenge
        fields = [
            'id',
            'title',
            'slug',
            'difficulty',
            'created_by',
            'created_at'
        ]


class ChallengeDetailSerializer(serializers.ModelSerializer):
    """Challenge detail with access control"""
    tags = TagSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField()
    sample_test_cases = serializers.SerializerMethodField()
    user_submission_status = serializers.SerializerMethodField()
    can_view = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = [
            'id',
            'title',
            'slug',
            'statement',
            'constraints',
            'input_format',
            'output_format',
            'difficulty',
            'tags',
            'created_by',
            'allow_public_practice_after_contest',
            'sample_test_cases',
            'user_submission_status',
            'can_view',
            'created_at',
            'updated_at',
        ]

    def get_sample_test_cases(self, obj):
        """Show sample testcases only if user has access"""
        if not self._can_access_challenge(obj):
            return []
        
        samples = obj.test_cases.filter(is_sample=True)
        return SampleChallengeTestCaseSerializer(samples, many=True).data

    def get_user_submission_status(self, obj):
        """Get user submission stats (practice challenges only)"""
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return None
        
        # Only show if user can view challenge
        if not self._can_access_challenge(obj):
            return None
        
        from submissions.models import Submission
        
        submissions = Submission.objects.filter(
            user=request.user,
            contest_item__challenge=obj
        )
        
        if not submissions.exists():
            return {
                'has_submitted': False,
                'best_verdict': None,
                'attempt_count': 0,
            }
        
        latest = submissions.latest('created_at')
        
        return {
            'has_submitted': True,
            'best_verdict': latest.status,
            'attempt_count': submissions.count(),
        }

    def get_can_view(self, obj):
        """Can user access this challenge"""
        return self._can_access_challenge(obj)

    def _can_access_challenge(self, obj):
        """
        Check access permission for challenge.
        
        Rules:
        - Creator: always
        - Superuser: always
        - Contest participant: during LIVE contest
        - Public practice: after contest ends (if enabled)
        """
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return False
        
        # Creator or superuser
        if obj.created_by == request.user or request.user.is_superuser:
            return True
        
        # Check if in LIVE contest
        from contest.models import ContestItem, ContestParticipant
        
        live_contests = ContestItem.objects.filter(
            challenge=obj,
            contest__state='LIVE'
        )
        
        for item in live_contests:
            if ContestParticipant.objects.filter(
                contest=item.contest,
                user=request.user
            ).exists():
                return True
        
        # Check if public practice is enabled and contest ended
        if obj.allow_public_practice_after_contest:
            ended_contests = ContestItem.objects.filter(
                challenge=obj,
                contest__state='ENDED'
            )
            if ended_contests.exists():
                return True
        
        return False


class ChallengeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = [
            'title',
            'slug',
            'statement',
            'constraints',
            'input_format',
            'output_format',
            'difficulty',
            'time_limit',
            'memory_limit',
            'tags',
            'allow_public_practice_after_contest',
        ]


class PracticeProblemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeProblem
        fields = [
            'id',
            'title',
            'slug',
            'difficulty',
            'created_at'
        ]


class PracticeProblemDetailSerializer(serializers.ModelSerializer):
    sample_test_cases = serializers.SerializerMethodField()
    user_submission_status = serializers.SerializerMethodField()

    class Meta:
        model = PracticeProblem
        fields = [
            'id',
            'title',
            'slug',
            'statement',
            'constraints',
            'input_format',
            'output_format',
            'difficulty',
            'time_limit',
            'memory_limit',
            'sample_test_cases',
            'user_submission_status',
            'created_at',
        ]

    def get_sample_test_cases(self, obj):
        samples = obj.test_cases.filter(is_sample=True)
        return [
            {
                'input_data': s.input_data,
                'expected_output': s.expected_output,
            }
            for s in samples
        ]

    def get_user_submission_status(self, obj):
        """Get user submission stats"""
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return None
        
        from submissions.models import Submission
        
        submissions = Submission.objects.filter(
            user=request.user,
            problem__id=obj.id
        )
        
        if not submissions.exists():
            return None
        
        latest = submissions.latest('created_at')
        return {
            'has_submitted': True,
            'best_verdict': latest.status,
            'attempt_count': submissions.count(),
        }


class PracticeProblemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeProblem
        fields = [
            'title',
            'slug',
            'statement',
            'constraints',
            'input_format',
            'output_format',
            'difficulty',
            'time_limit',
            'memory_limit',
            'tags',
        ]
