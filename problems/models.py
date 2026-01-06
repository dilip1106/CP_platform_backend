# Create your models here.
from django.db import models
from django.utils.text import slugify
from django.conf import settings
User = settings.AUTH_USER_MODEL
from django.utils import timezone
class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True, blank=True)  # keep blank=True for now

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # Ensure slug is unique
            while Tag.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)



class Problem(models.Model):
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

    tags = models.ManyToManyField(Tag, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_problems'
    )

    # is_published = models.BooleanField(default=True)
    state = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default='DRAFT',
        db_index=True
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            i = 1
            while Problem.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)


    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['state']),
            models.Index(fields=['created_at']),
        ]



class ProblemTestCase(models.Model):
    """Test cases for problems"""
    problem = models.ForeignKey(
        Problem,
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
            models.Index(fields=['problem']),
            models.Index(fields=['is_sample']),
            models.Index(fields=['is_hidden']),
        ]


    def __str__(self):
        return f"{self.problem.title} - TC{self.id}"
