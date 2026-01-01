from django.db import models
from django.conf import settings
from django.utils.timezone import now

User = settings.AUTH_USER_MODEL


class Contest(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    description = models.TextField(blank=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_contests'
    )

    managers = models.ManyToManyField(
        User,
        blank=True,
        related_name='managed_contests'
    )

    is_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    # ADD THESE FIELDS
    STATE_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SCHEDULED', 'Scheduled'),
        ('LIVE', 'Live'),
        ('ENDED', 'Ended'),
        ('ARCHIVED', 'Archived'),
    ]
    
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='DRAFT',
        help_text="Contest lifecycle state"
    )
    
    is_published = models.BooleanField(
        default=False,
        help_text="Only SCHEDULED+ contests are visible to participants"
    )
    
    logo = models.URLField(blank=True, null=True)
    rules = models.TextField(blank=True)
    
    # TIMESTAMPS (for automatic state transitions)
    published_at = models.DateTimeField(null=True, blank=True)
    last_state_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.state})"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['state', 'start_time']),
            models.Index(fields=['is_published']),
        ]


class ContestProblem(models.Model):
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='contest_problems'
    )
    problem = models.ForeignKey(
        'problems.Problem',
        on_delete=models.CASCADE
    )

    order = models.PositiveIntegerField(
        help_text="Order of problem in contest (A=1, B=2...)"
    )

    class Meta:
        unique_together = ('contest', 'problem')
        ordering = ['order']

    def __str__(self):
        return f"{self.contest.title} - {self.problem.title}"



class ContestParticipant(models.Model):
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contest_participations'
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('contest', 'user')

    def __str__(self):
        return f"{self.user} -> {self.contest.title}"


class ContestRegistration(models.Model):
    """
    Track user registrations for contests
    Different from ContestParticipant - registration happens before contest
    Participant is created when user actually participates
    """
    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('PARTICIPATED', 'Participated'),
        ('CANCELLED', 'Cancelled'),
    ]

    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contest_registrations'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REGISTERED'
    )
    
    registered_at = models.DateTimeField(auto_now_add=True)
    participated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('contest', 'user')
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.user} - {self.contest.title} ({self.status})"
