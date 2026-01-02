from rest_framework import serializers
from .models import Challenge, ChallengeTestCase, PracticeProblem, PracticeProblemTestCase
from problems.serializers import TagSerializer


# ========================
# CHALLENGE SERIALIZERS
# ========================

class ChallengeTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeTestCase
        fields = [
            'id',
            'input_data',
            'expected_output',
            'is_sample',
            'is_hidden',
        ]


class SampleChallengeTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeTestCase
        fields = ['input_data', 'expected_output']


class ChallengeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField()

    class Meta:
        model = Challenge
        fields = [
            'id',
            'title',
            'slug',
            'difficulty',
            'tags',
            'created_by',
            'created_at',
        ]


class ChallengeDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField()
    sample_test_cases = serializers.SerializerMethodField()

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
            'created_at',
            'updated_at',
        ]

    def get_sample_test_cases(self, obj):
        samples = obj.test_cases.filter(is_sample=True)
        return SampleChallengeTestCaseSerializer(samples, many=True).data


class ChallengeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=__import__('problems.models', fromlist=['Tag']).Tag.objects.all(),
        many=True,
        required=False
    )

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
            'tags',
            'allow_public_practice_after_contest',
        ]

    def validate(self, attrs):
        if 'slug' in attrs:
            # Check if slug is unique (excluding current instance on update)
            instance = self.instance
            qs = Challenge.objects.filter(slug=attrs['slug'])
            if instance:
                qs = qs.exclude(id=instance.id)
            if qs.exists():
                raise serializers.ValidationError({'slug': 'This slug already exists'})
        return attrs


# ========================
# PRACTICE PROBLEM SERIALIZERS
# ========================

class PracticeProblemTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeProblemTestCase
        fields = [
            'id',
            'input_data',
            'expected_output',
            'is_sample',
        ]


class SamplePracticeProblemTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeProblemTestCase
        fields = ['input_data', 'expected_output']


class PracticeProblemListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField()

    class Meta:
        model = PracticeProblem
        fields = [
            'id',
            'title',
            'slug',
            'difficulty',
            'tags',
            'created_by',
            'created_at',
        ]


class PracticeProblemDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    created_by = serializers.StringRelatedField()
    sample_test_cases = serializers.SerializerMethodField()

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
            'tags',
            'created_by',
            'sample_test_cases',
            'created_at',
            'updated_at',
        ]

    def get_sample_test_cases(self, obj):
        samples = obj.test_cases.filter(is_sample=True)
        return SamplePracticeProblemTestCaseSerializer(samples, many=True).data


class PracticeProblemCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=__import__('problems.models', fromlist=['Tag']).Tag.objects.all(),
        many=True,
        required=False
    )

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

    def validate(self, attrs):
        if 'slug' in attrs:
            instance = self.instance
            qs = PracticeProblem.objects.filter(slug=attrs['slug'])
            if instance:
                qs = qs.exclude(id=instance.id)
            if qs.exists():
                raise serializers.ValidationError({'slug': 'This slug already exists'})

        if 'time_limit' in attrs and attrs['time_limit'] <= 0:
            raise serializers.ValidationError({'time_limit': 'Must be positive'})

        if 'memory_limit' in attrs and attrs['memory_limit'] <= 0:
            raise serializers.ValidationError({'memory_limit': 'Must be positive'})

        return attrs
