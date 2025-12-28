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


class ProblemListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)

    class Meta:
        model = Problem
        fields = [
            'id',
            'title',
            'slug',
            'difficulty',
            'tags'
        ]


class ProblemDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    sample_test_cases = serializers.SerializerMethodField()

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
            'sample_test_cases'
        ]

    def get_sample_test_cases(self, obj):
        samples = obj.test_cases.filter(is_sample=True)
        return SampleTestCaseSerializer(samples, many=True).data
