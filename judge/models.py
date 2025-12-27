import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
class Problem(models.Model):
    """
    Stores the DSA problem statement, metadata, and constraints.
    """
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate slug from title (e.g., "Two Sum" -> "two-sum")
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    statement = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    
    # Constraints
    time_limit_ms = models.PositiveIntegerField(default=1000, help_text="Time limit in milliseconds")
    memory_limit_kb = models.PositiveIntegerField(default=256000, help_text="Memory limit in kilobytes")
    
    category = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.difficulty})"

class TestCase(models.Model):
    """
    Stores input and expected output for judging. 
    Can be marked as 'sample' to show to users.
    """
    problem = models.ForeignKey(
        Problem, 
        on_delete=models.CASCADE, 
        related_name='test_cases'
    )
    input_data = models.TextField()
    expected_output = models.TextField()
    is_sample = models.BooleanField(default=False)
    
    # Optional: hidden notes for admins
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"TC for {self.problem.title} (Sample: {self.is_sample})"

class Contest(models.Model):
    """
    Manages timed events where users solve specific problems.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    problems = models.ManyToManyField(Problem, related_name='contests', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.start_time <= now <= self.end_time

class Submission(models.Model):
    """
    Stores user-submitted code and the resulting judge status.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Time Limit Exceeded', 'TLE'),
        ('Memory Limit Exceeded', 'MLE'),
        ('Runtime Error', 'Runtime Error'),
        ('Compilation Error', 'Compilation Error'),
    ]

    LANGUAGE_CHOICES = [
        ('python', 'Python 3'),
        ('cpp', 'C++ 17'),
        ('java', 'Java 11'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='submissions'
    )
    problem = models.ForeignKey(
        Problem, 
        on_delete=models.CASCADE, 
        related_name='submissions'
    )
    contest = models.ForeignKey(
        Contest, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='submissions'
    )
    
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    source_code = models.TextField()
    
    # Judge Results
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    execution_time_ms = models.IntegerField(null=True, blank=True)
    memory_usage_kb = models.IntegerField(null=True, blank=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.problem.title} [{self.status}]"