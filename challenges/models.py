from django.db import models
from django.conf import settings
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


class Challenge(models.Model):
    """
    Manager-created challenges that can become public practice problems
    after the contest ends (if allow_public_practice_after_contest=True)
    """
    DIFFICULTY_CHOICES = [
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    statement = models.TextField()
    constraints = models.TextField(blank=True)
    input_format = models.TextField()
    output_format = models.TextField()

    difficulty = models.CharField(max_length=1, choices=DIFFICULTY_CHOICES)

    tags = models.ManyToManyField('problems.Tag', blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_challenges'
    )

    # Control if this becomes public practice after contest ends
    allow_public_practice_after_contest = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_by']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ChallengeTestCase(models.Model):
    """Test cases for challenges"""
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name='test_cases'
    )

    input_data = models.TextField()
    expected_output = models.TextField()

    is_sample = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.challenge.title} - TC{self.id}"


class PracticeProblem(models.Model):
    """
    Superuser-created practice-only problems.
    These are NOT part of contests, only for practice.
    Always public to authenticated users.
    """
    DIFFICULTY_CHOICES = [
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    statement = models.TextField()
    constraints = models.TextField(blank=True)
    input_format = models.TextField()
    output_format = models.TextField()

    difficulty = models.CharField(max_length=1, choices=DIFFICULTY_CHOICES)
    time_limit = models.IntegerField(help_text="Time limit in ms")
    memory_limit = models.IntegerField(help_text="Memory limit in MB")

    tags = models.ManyToManyField('problems.Tag', blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_practice_problems'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_by']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PracticeProblemTestCase(models.Model):
    """Test cases for practice problems"""
    problem = models.ForeignKey(
        PracticeProblem,
        on_delete=models.CASCADE,
        related_name='test_cases'
    )

    input_data = models.TextField()
    expected_output = models.TextField()
    is_sample = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.problem.title} - TC{self.id}"
