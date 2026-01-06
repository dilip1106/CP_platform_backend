from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
User = settings.AUTH_USER_MODEL


class Challenge(models.Model):
    """
    Manager-owned private problems for contests.
    
    CRITICAL RULES:
    - Created ONLY by managers (enforced in clean())
    - Visible ONLY to creator and superusers
    - Can be added to contests
    - Has testcases
    - NOT publicly visible
    """
    DIFFICULTY_CHOICES = [
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    ]

    STATE_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
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
        related_name='created_challenges'
    )

    allow_public_practice_after_contest = models.BooleanField(
        default=False,
        help_text="Allow public practice after contest ends"
    )
    
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='DRAFT',
        db_index=True
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_by']),
            models.Index(fields=['state']),
        ]

    def clean(self):
        """
        CRITICAL: Enforce that only managers can create challenges.
        
        Rules:
        - created_by must be manager or superuser
        """
        if self.created_by and not self.created_by.is_superuser:
            if self.created_by.role != 'MANAGER':
                raise ValidationError(
                    "Challenges can only be created by managers or superusers"
                )

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            i = 1
            while Challenge.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug

        self.clean()
        super().save(*args, **kwargs)

    def is_visible_to_user(self, user):
        """
        Check if challenge is visible to user.
        
        Rules:
        - Creator always sees it
        - Superuser always sees it
        - Contest participants see it during LIVE contests
        - Public practice after contest (if enabled)
        """
        if not user:
            return False
        
        # Creator or superuser
        if user.is_superuser or user == self.created_by:
            return True

        # Check if user is in a LIVE contest with this challenge
        from contest.models import ContestItem, ContestParticipant
        
        live_contests = ContestItem.objects.filter(
            challenge=self,
            contest__state='LIVE'
        )
        
        if self.state != 'PUBLISHED':
            return user.is_superuser or user == self.created_by

        for item in live_contests:
            if ContestParticipant.objects.filter(
                contest=item.contest,
                user=user
            ).exists():
                return True
        
        # Check public practice after contest
        if self.allow_public_practice_after_contest:
            from django.utils.timezone import now
            ended_contests = ContestItem.objects.filter(
                challenge=self,
                contest__end_time__lt=now()
            )
            if ended_contests.exists():
                return True
        
        return False

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
        indexes = [
            models.Index(fields=['challenge']),
            models.Index(fields=['is_sample']),
        ]

    def __str__(self):
        return f"{self.challenge.title} - TC{self.id}"


class PracticeProblem(models.Model):
    """
    Practice problems (non-contest).
    
    ⚠️ TECHNICAL DEBT: Duplicated with Problem model.
    Future refactor: Merge into Problem with problem_type field.
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

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_by']),
        ]

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
        indexes = [
            models.Index(fields=['problem']),
            models.Index(fields=['is_sample']),
        ]

    def __str__(self):
        return f"{self.problem.title} - TC{self.id}"
