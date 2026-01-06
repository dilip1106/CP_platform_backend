from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils import timezone
User = settings.AUTH_USER_MODEL


class Contest(models.Model):
    """
    Contest model with enforced state transitions.
    
    Valid transitions:
    DRAFT → SCHEDULED → LIVE → ENDED → ARCHIVED
    DRAFT → ARCHIVED (skip)
    SCHEDULED → ARCHIVED (skip)
    """
    STATE_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SCHEDULED', 'Scheduled'),
        ('LIVE', 'Live'),
        ('ENDED', 'Ended'),
        ('ARCHIVED', 'Archived'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField()
    
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='DRAFT',
        db_index=True
    )
    
    is_public = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_contests'
    )
    
    managers = models.ManyToManyField(
        User,
        related_name='managed_contests',
        blank=True
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['state']),
            models.Index(fields=['created_by']),
            models.Index(fields=['start_time']),
        ]

    def can_transition_to(self, new_state):
        """
        Check if transition from current state to new_state is valid.
        
        Valid transitions:
        - DRAFT → SCHEDULED, ARCHIVED
        - SCHEDULED → LIVE, ARCHIVED
        - LIVE → ENDED
        - ENDED → ARCHIVED
        - ARCHIVED → (none)
        """
        allowed = {
            'DRAFT': ['SCHEDULED', 'ARCHIVED'],
            'SCHEDULED': ['LIVE', 'ARCHIVED'],
            'LIVE': ['ENDED'],
            'ENDED': ['ARCHIVED'],
            'ARCHIVED': [],
        }
        return new_state in allowed.get(self.state, [])

    def clean(self):
        """Validate contest state and transitions"""
        # Don't allow invalid state transitions
        if self.pk:  # Only check on update
            original = Contest.objects.get(pk=self.pk)
            if original.state != self.state:
                if not self.can_transition_to(self.state):
                    raise ValidationError(
                        f"Cannot transition from {original.state} to {self.state}"
                    )

        # Validate time constraints
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        
        


    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            i = 1
            while Contest.objects.filter(slug=slug).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug

        self.clean()
        super().save(*args, **kwargs)

    @property
    def time_remaining_seconds(self):
        """Get seconds until contest ends"""
        delta = self.end_time - now()
        return max(0, int(delta.total_seconds()))

    @property
    def time_until_start_seconds(self):
        """Get seconds until contest starts"""
        delta = self.start_time - now()
        return max(0, int(delta.total_seconds()))

    def is_draft(self):
        return self.state == 'DRAFT'

    def is_scheduled(self):
        return self.state == 'SCHEDULED'

    def is_live(self):
        current_time = now()
        return self.state == 'LIVE' and self.start_time <= current_time < self.end_time

    def is_ended(self):
        return self.state == 'ENDED' or now() >= self.end_time
    
    
    
    def is_visible_to_user(self, user):
        # Public + published + not draft
        if self.is_public and self.is_published and self.state != 'DRAFT':
            return True

        if not user:
            return False

        if user.is_superuser:
            return True

        if self.managers.filter(id=user.id).exists():
            return True

        if self.state in ['LIVE', 'ENDED'] and self.participants.filter(user=user).exists():
            return True

        return False



    def __str__(self):
        return f"{self.title} ({self.state})"


class ContestItem(models.Model):
    """
    Unified model for contest problems and challenges.
    
    CRITICAL INVARIANT: Exactly ONE of problem or challenge must be set.
    Enforced at:
    - Database constraint (CheckConstraint)
    - Model validation (clean())
    
    item_type is now a @property, not a field
    Derived dynamically from problem/challenge
    """
    ITEM_TYPE_CHOICES = [
        ('PROBLEM', 'Problem'),
        ('CHALLENGE', 'Challenge'),
    ]
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='contest_items'
    )
    
    # EXACTLY ONE must be set
    problem = models.ForeignKey(
        'problems.Problem',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='contest_appearances'
    )
    challenge = models.ForeignKey(
        'challenges.Challenge',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='contest_appearances'
    )
    
    order = models.PositiveIntegerField(
        help_text="Order in contest (A=1, B=2, ...)"
    )
    score = models.IntegerField(default=100)

    
    item_type = models.CharField(
        max_length=10,
        choices=ITEM_TYPE_CHOICES,
        editable=False
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = [
            ('contest', 'problem'),
            ('contest', 'challenge'),
            ('contest', 'order'),
        ]
        indexes = [
            models.Index(fields=['contest', 'order']),
            models.Index(fields=['problem']),
            models.Index(fields=['challenge']),
        ]
        constraints = [
            # CRITICAL: Enforce exactly one source at database level
            models.CheckConstraint(
                check=(
                    models.Q(problem__isnull=False, challenge__isnull=True) |
                    models.Q(problem__isnull=True, challenge__isnull=False)
                ),
                name="contestitem_single_source"
            ),
        ]

    def clean(self):
        """Ensure exactly one of problem or challenge is set"""
        if not self.problem and not self.challenge:
            raise ValidationError("Either problem or challenge must be set")
        
        if self.problem and self.challenge:
            raise ValidationError("Cannot set both problem and challenge")

    def save(self, *args, **kwargs):
        # Set item_type dynamically before saving
        if self.problem:
            self.item_type = 'PROBLEM'
        elif self.challenge:
            self.item_type = 'CHALLENGE'
        else:
            self.item_type = ''
        super().save(*args, **kwargs)

    @property
    def item_type(self):
        """Dynamically derive item type (no sync issues)"""
        if self.problem:
            return 'PROBLEM'
        elif self.challenge:
            return 'CHALLENGE'
        return None

    def get_item(self):
        """Return the actual problem or challenge instance"""
        return self.problem or self.challenge

    def __str__(self):
        item_name = self.problem.title if self.problem else self.challenge.title
        return f"{self.contest.title} - {item_name} (Order: {self.order})"


class ContestParticipant(models.Model):
    """Track contest participants"""
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
        indexes = [
            models.Index(fields=['contest', 'user']),
        ]

    def __str__(self):
        return f"{self.user} in {self.contest}"


class ContestRegistration(models.Model):
    """Track contest registrations"""
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
        indexes = [
            models.Index(fields=['contest', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user} - {self.contest} ({self.status})"
