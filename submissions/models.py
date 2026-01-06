# submissions/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.db.models import Q
User = settings.AUTH_USER_MODEL
from django.utils import timezone

class Submission(models.Model):
    """
    User code submissions for problems/contests.
    
    CRITICAL RULES:
    - Either problem (practice) OR contest_item (contest)
    - Never both
    - If contest_item is set, contest MUST be set
    - contest_item.contest MUST equal contest
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('AC', 'Accepted'),
        ('WA', 'Wrong Answer'),
        ('TLE', 'Time Limit Exceeded'),
        ('MLE', 'Memory Limit Exceeded'),
        ('RE', 'Runtime Error'),
        ('CE', 'Compilation Error'),
    ]

    LANGUAGE_CHOICES = [
        ('PYTHON', 'Python 3'),
        ('JAVA', 'Java'),
        ('CPP', 'C++'),
        ('C', 'C'),
        ('JS', 'JavaScript'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    
    # EITHER problem (practice) OR contest_item (contest) - NEVER BOTH
    problem = models.ForeignKey(
        'problems.Problem',
        on_delete=models.CASCADE,
        related_name='submissions',
        null=True,
        blank=True,
        help_text="For practice submissions"
    )
    
    contest_item = models.ForeignKey(
        'contest.ContestItem',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='submissions',
        help_text="For contest submissions"
    )
    
    contest = models.ForeignKey(
        'contest.Contest',
        on_delete=models.CASCADE,
        related_name='submissions',
        null=True,
        blank=True,
        help_text="Contest reference (for consistency & leaderboard)"
    )
    
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    source_code = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'problem']),
            models.Index(fields=['user', 'contest_item']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['contest']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(problem__isnull=False, contest_item__isnull=True) |
                    Q(problem__isnull=True, contest_item__isnull=False)
                ),
                name="submission_single_target"
            ),
            models.UniqueConstraint(
                fields=['user', 'contest_item'],
                condition=Q(status='AC'),
                name='single_ac_per_contest_item'
            ),
        ]


    def clean(self):
        """
        CRITICAL: Enforce submission consistency.
        
        Rules:
        1. Exactly one: problem OR contest_item
        2. If contest_item: contest MUST be set
        3. If contest_item: contest_item.contest == contest
        """
        # Rule 1: Exactly one submission target
        if not self.problem and not self.contest_item:
            raise ValidationError(
                "Submission must have either problem (practice) or contest_item (contest)"
            )
        
        if self.problem and self.contest_item:
            raise ValidationError(
                "Submission cannot be for both problem and contest_item"
            )

        # Rule 2: Contest submission must have contest
        if self.contest_item and not self.contest:
            raise ValidationError(
                "Contest submission must have contest field set"
            )

        # Rule 3: Contest item must belong to the specified contest
        if self.contest_item and self.contest:
            if self.contest_item.contest_id != self.contest_id:
                raise ValidationError(
                    "contest_item does not belong to the specified contest"
                )

    def save(self, *args, **kwargs):
        """Validate before saving"""
        self.clean()
        super().save(*args, **kwargs)

    def get_item(self):
        """Get the actual problem or challenge being solved"""
        if self.problem:
            return self.problem
        if self.contest_item:
            return self.contest_item.get_item()
        return None

    def get_item_type(self):
        """Return 'problem' or 'challenge' or None"""
        if self.problem:
            return 'problem'
        if self.contest_item:
            return self.contest_item.item_type.lower()
        return None

    def get_time_limit_ms(self):
        """Get time limit from item"""
        item = self.get_item()
        return item.time_limit if item else None

    def get_memory_limit_mb(self):
        """Get memory limit from item"""
        item = self.get_item()
        return item.memory_limit if item else None

    def __str__(self):
        item = self.get_item()
        item_name = item.title if item else 'Unknown'
        return f"{self.user} | {item_name} | {self.status}"


class SubmissionResult(models.Model):
    """
    Individual testcase result for a submission.
    
    CRITICAL RULES:
    - NEVER expose hidden testcase details publicly
    - Only owner, manager, or superuser can see details
    - After contest ends, hidden testcases can be shown
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('AC', 'Accepted'),
        ('WA', 'Wrong Answer'),
        ('TLE', 'Time Limit Exceeded'),
        ('MLE', 'Memory Limit Exceeded'),
        ('RE', 'Runtime Error'),
        ('CE', 'Compilation Error'),
        ('ERROR', 'System Error'),
    ]

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='results'
    )
    
    # Store testcase metadata
    test_case_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of the test case"
    )
    test_case_type = models.CharField(
        max_length=20,
        choices=[
            ('PROBLEM', 'Problem Test Case'),
            ('CHALLENGE', 'Challenge Test Case'),
            ('PRACTICE', 'Practice Problem Test Case'),
        ],
        default='PROBLEM'
    )

    # Cached testcase data (for access control)
    is_sample = models.BooleanField(default=False)
    input_data = models.TextField(null=True, blank=True)
    expected_output = models.TextField(null=True, blank=True)
    
    # Results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    actual_output = models.TextField(null=True, blank=True)
    stderr = models.TextField(null=True, blank=True)
    
    # Metrics
    execution_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="Execution time in ms"
    )
    memory_used = models.IntegerField(
        null=True,
        blank=True,
        help_text="Memory used in MB"
    )

    created_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['submission']),
            models.Index(fields=['submission', 'status']),
            models.Index(fields=['submission', 'is_sample']),
            models.Index(fields=['test_case_type']),
        ]

    def can_view_details(self, user):
        submission = self.submission

        if not user:
            return False

        # Superuser always sees
        if user.is_superuser:
            return True

        # Owner always sees
        if user == submission.user:
            return True

        # Contest manager sees
        if submission.contest:
            contest = submission.contest
            if contest.created_by_id == user.id or contest.managers.filter(id=user.id).exists():
                return True

            # Contest participants logic
            if contest.is_live():
                return self.is_sample

            if contest.is_ended():
                return True

        return False


    def is_passed(self):
        """Check if test case passed"""
        return self.status == 'AC'

    def get_test_case_object(self):
        """Get the actual test case object"""
        if self.test_case_type == 'PROBLEM':
            from problems.models import ProblemTestCase
            try:
                return ProblemTestCase.objects.get(id=self.test_case_id)
            except ProblemTestCase.DoesNotExist:
                return None
        elif self.test_case_type == 'CHALLENGE':
            from challenges.models import ChallengeTestCase
            try:
                return ChallengeTestCase.objects.get(id=self.test_case_id)
            except ChallengeTestCase.DoesNotExist:
                return None
        elif self.test_case_type == 'PRACTICE':
            from challenges.models import PracticeProblemTestCase
            try:
                return PracticeProblemTestCase.objects.get(id=self.test_case_id)
            except PracticeProblemTestCase.DoesNotExist:
                return None
        return None

    def __str__(self):
        return f"Result {self.id} - {self.status}"