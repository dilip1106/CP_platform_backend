from rest_framework import serializers
from django.utils.timezone import now
from .models import Submission, SubmissionResult


class SubmissionResultSerializer(serializers.ModelSerializer):
    """
    SubmissionResult serializer with STRICT access control.
    
    Rules:
    - Input/output visible ONLY to:
      - Submission owner
      - Contest manager
      - Superuser
    - Hidden testcases NEVER exposed during contest
    """
    test_case_input = serializers.SerializerMethodField()
    expected_output_value = serializers.SerializerMethodField()
    actual_output_value = serializers.SerializerMethodField()
    stderr_output = serializers.SerializerMethodField()

    class Meta:
        model = SubmissionResult
        fields = [
            'id',
            'is_sample',
            'test_case_input',
            'expected_output_value',
            'actual_output_value',
            'stderr_output',
            'status',
            'execution_time',
            'memory_used'
        ]

    def get_test_case_input(self, obj):
        """Show input only if authorized and appropriate timing"""
        if not obj.can_view_details(self.context['request'].user):
            return None
        
        # During contest: only sample testcases
        if self._is_contest_ongoing(obj):
            if not obj.is_sample:
                return None
        
        return obj.input_data

    def get_expected_output_value(self, obj):
        """Show expected output only if authorized"""
        if not obj.can_view_details(self.context['request'].user):
            return None
        
        # During contest: only sample testcases
        if self._is_contest_ongoing(obj):
            if not obj.is_sample:
                return None
        
        return obj.expected_output

    def get_actual_output_value(self, obj):
        """Show actual output only if authorized"""
        if not obj.can_view_details(self.context['request'].user):
            return None
        return obj.actual_output

    def get_stderr_output(self, obj):
        """Show stderr only if authorized"""
        if not obj.can_view_details(self.context['request'].user):
            return None
        return obj.stderr

    def _is_contest_ongoing(self, obj):
        """Check if contest is still ongoing"""
        submission = obj.submission
        if not submission.contest:
            return False
        return now() < submission.contest.end_time


class SubmissionSerializer(serializers.ModelSerializer):
    """Submission serializer with user-specific data"""
    item_title = serializers.SerializerMethodField()
    item_type = serializers.SerializerMethodField()
    source_code = serializers.SerializerMethodField()
    results = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            'id',
            'item_type',
            'item_title',
            'language',
            'status',
            'source_code',
            'created_at',
            'results'
        ]

    def get_item_title(self, obj):
        """Get problem or challenge title"""
        item = obj.get_item()
        return item.title if item else 'Unknown'

    def get_item_type(self, obj):
        """Return 'problem' or 'challenge'"""
        return obj.get_item_type()

    def get_source_code(self, obj):
        """Show source code only to owner or manager"""
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return None
        
        # Owner always sees
        if obj.user == request.user:
            return obj.source_code
        
        # Superuser sees
        if request.user.is_superuser:
            return obj.source_code
        
        # Contest manager sees
        if obj.contest:
            is_manager = (
                obj.contest.created_by == request.user or
                request.user in obj.contest.managers.all()
            )
            if is_manager:
                return obj.source_code
        
        return None

    def get_results(self, obj):
        """Return results with proper access control"""
        return SubmissionResultSerializer(
            obj.results.all().order_by('id'),
            many=True,
            context=self.context
        ).data


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating submissions"""
    problem_id = serializers.IntegerField(required=False, allow_null=True)
    contest_item_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Submission
        fields = [
            'problem_id',
            'contest_item_id',
            'language',
            'source_code'
        ]

    def validate(self, attrs):
        """Ensure exactly one submission target"""
        problem_id = attrs.get('problem_id')
        contest_item_id = attrs.get('contest_item_id')
        
        if not problem_id and not contest_item_id:
            raise serializers.ValidationError(
                "Either problem_id or contest_item_id must be provided"
            )
        
        if problem_id and contest_item_id:
            raise serializers.ValidationError(
                "Cannot submit to both problem and contest_item"
            )
        
        return attrs

    def create(self, validated_data):
        """Create submission with proper item assignment"""
        problem_id = validated_data.pop('problem_id', None)
        contest_item_id = validated_data.pop('contest_item_id', None)
        
        submission = Submission(**validated_data)
        
        if problem_id:
            submission.problem_id = problem_id
            submission.contest = None
        elif contest_item_id:
            from contest.models import ContestItem
            contest_item = ContestItem.objects.get(id=contest_item_id)
            submission.contest_item = contest_item
            submission.contest = contest_item.contest
        
        submission.full_clean()
        submission.save()
        return submission
