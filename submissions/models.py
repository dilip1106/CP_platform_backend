# submissions/models.py
from django.db import models
from django.conf import settings
from problems.models import Problem, ProblemTestCase

class Submission(models.Model):
    class LanguageChoices(models.TextChoices):
        PYTHON = 'PY', 'Python'
        CPP = 'CPP', 'C++'
        JAVA = 'JAVA', 'Java'

    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        ACCEPTED = 'AC', 'Accepted'
        WRONG_ANSWER = 'WA', 'Wrong Answer'
        TIME_LIMIT = 'TLE', 'Time Limit Exceeded'
        RUNTIME_ERROR = 'RE', 'Runtime Error'
        COMPILE_ERROR = 'CE', 'Compile Error'
        ERROR = 'ERROR', 'Error'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='submissions')
    language = models.CharField(max_length=10, choices=LanguageChoices.choices)
    source_code = models.TextField()
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    memory_usage_kb = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} | {self.problem} | {self.status}"


class SubmissionResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='results')
    test_case = models.ForeignKey(ProblemTestCase, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Submission.StatusChoices.choices)
    stdout = models.TextField(null=True, blank=True)
    stderr = models.TextField(null=True, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    memory_usage_kb = models.IntegerField(null=True, blank=True)
