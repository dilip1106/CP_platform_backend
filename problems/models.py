# Create your models here.
from django.db import models
from django.utils.text import slugify

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Problem(models.Model):
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

    tags = models.ManyToManyField(Tag, blank=True)

    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProblemTestCase(models.Model):
    problem = models.ForeignKey(
        Problem,
        related_name='test_cases',
        on_delete=models.CASCADE
    )

    input_data = models.TextField()
    expected_output = models.TextField()

    is_sample = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.problem.title} | Sample={self.is_sample}"
