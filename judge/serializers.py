from rest_framework import serializers
from .models import Problem, TestCase, Submission, Contest

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ['id', 'problem', 'input_data', 'expected_output', 'is_sample']

class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = ['id', 'title', 'slug', 'statement', 'difficulty', 'category', 'time_limit_ms', 'memory_limit_kb']

class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'problem', 'language', 'source_code', 'status', 'submitted_at']
        read_only_fields = ['status']

class ContestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contest
        fields = '__all__'