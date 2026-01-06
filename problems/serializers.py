from rest_framework import serializers
from .models import Problem, ProblemTestCase, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class SampleTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemTestCase
        fields = ['input_data', 'expected_output']


class UserSubmissionStatusSerializer(serializers.Serializer):
    """User-specific submission metadata for a problem"""
    has_submitted = serializers.BooleanField()
    best_verdict = serializers.CharField(allow_null=True)
    attempt_count = serializers.IntegerField()
    last_submission_at = serializers.DateTimeField(allow_null=True)
    passed_testcases = serializers.IntegerField()
    total_testcases = serializers.IntegerField()


class ProblemListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    user_status = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = [
            'id',
            'title',
            'slug',
            'difficulty',
            'tags',
            'user_status'
        ]

    def get_user_status(self, obj):
        """Get user-specific status (LeetCode-style)"""
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return None
        
        return self._compute_submission_status(obj, request.user)

    def _compute_submission_status(self, problem, user):
        """Compute submission statistics for user"""
        from submissions.models import Submission
        
        submissions = Submission.objects.filter(
            user=user,
            problem=problem
        )
        
        if not submissions.exists():
            return {
                'has_submitted': False,
                'best_verdict': None,
                'attempt_count': 0,
                'last_submission_at': None,
                'passed_testcases': 0,
                'total_testcases': 0,
            }
        
        # Get verdict distribution
        verdicts = submissions.values_list('status', flat=True)
        best_verdict = 'AC' if 'AC' in verdicts else verdicts.first()
        
        # Get latest submission
        latest = submissions.latest('created_at')
        
        # Count testcases
        passed = latest.results.filter(status='AC').count()
        total = latest.results.count() or problem.test_cases.count()
        
        return {
            'has_submitted': True,
            'best_verdict': best_verdict,
            'attempt_count': submissions.count(),
            'last_submission_at': latest.created_at,
            'passed_testcases': passed,
            'total_testcases': total,
        }


class ProblemDetailSerializer(serializers.ModelSerializer):
    """Problem detail with user-specific status"""
    tags = TagSerializer(many=True)
    sample_test_cases = serializers.SerializerMethodField()
    user_submission_status = serializers.SerializerMethodField()
    failed_testcases = serializers.SerializerMethodField()

    class Meta:
        model = Problem
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
            'tags',
            'sample_test_cases',
            'user_submission_status',
            'failed_testcases'
        ]

    def get_sample_test_cases(self, obj):
        """Return sample test cases"""
        samples = obj.test_cases.filter(is_sample=True)
        return SampleTestCaseSerializer(samples, many=True).data

    def get_user_submission_status(self, obj):
        """
        Get submission status for authenticated user.
        Returns None for anonymous users.
        """
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return None
        
        from submissions.models import Submission
        
        # Get all submissions for this problem by user
        submissions = Submission.objects.filter(
            user=request.user,
            problem=obj
        ).select_related('user')
        
        if not submissions.exists():
            return {
                'has_submitted': False,
                'best_verdict': None,
                'last_submission_at': None,
                'passed_testcases': 0,
                'total_testcases': 0,
            }
        
        # Get latest submission
        latest = submissions.latest('created_at')
        
        # Count testcases passed
        passed = latest.results.filter(status='AC').count()
        total = latest.results.count() or obj.test_cases.count()
        
        return {
            'has_submitted': True,
            'best_verdict': latest.status,
            'last_submission_at': latest.created_at,
            'passed_testcases': passed,
            'total_testcases': total,
        }

    def get_failed_testcases(self, obj):
        """
        Return failed testcases (with access control).
        
        ONLY shown to:
        - Submission owner
        - Superuser
        """
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return []
        
        if request.user.is_superuser:
            return []
        
        from submissions.models import Submission, SubmissionResult
        
        # Get latest submission by user
        try:
            latest = Submission.objects.filter(
                user=request.user,
                problem=obj
            ).latest('created_at')
        except Submission.DoesNotExist:
            return []
        
        # Get failed results
        failed_results = latest.results.filter(
            status__in=['WA', 'TLE', 'RE', 'CE']
        ).order_by('id')
        
        return [
            {
                'id': result.id,
                'testcase_id': result.test_case_id,
                'status': result.status,
                'input': result.input_data if result.is_sample else None,
                'expected': result.expected_output if result.is_sample else None,
                'actual': result.actual_output,
                'error': result.stderr if result.status == 'CE' else None,
            }
            for result in failed_results
        ]
