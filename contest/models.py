from django.db import models
from django.conf import settings

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

    def __str__(self):
        return self.title


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
