from rest_framework import serializers
from .models import Submission, SubmissionResult

# -------------------------
# Test Case Result Serializer
# -------------------------
class SubmissionResultSerializer(serializers.ModelSerializer):
    test_case_input = serializers.CharField(source='test_case.input_data', read_only=True)
    expected_output = serializers.CharField(source='test_case.expected_output', read_only=True)
    is_sample = serializers.BooleanField(source='test_case.is_sample', read_only=True)

    class Meta:
        model = SubmissionResult
        fields = [
            'id',
            'test_case_input',
            'expected_output',
            'is_sample',
            'status',
            'stdout',
            'stderr',
            'execution_time_ms',
            'memory_usage_kb'
        ]


# -------------------------
# Submission Serializer
# -------------------------
class SubmissionSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    results = SubmissionResultSerializer(many=True, read_only=True)


    class Meta:
        model = Submission
        fields = [
            'id',
            'problem',
            'problem_title',
            'language',
            'status',
            'execution_time_ms',
            'memory_usage_kb',
            'created_at',
            'results'  # Include all test case results
        ]


# -------------------------
# Create Submission Serializer
# -------------------------
class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['problem', 'language', 'source_code']

    def validate_language(self, value):
        from .languages import LANGUAGE_CONFIG
        if value not in LANGUAGE_CONFIG:
            raise serializers.ValidationError("Unsupported language")
        return value
