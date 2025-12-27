from django.contrib import admin
from .models import Problem, TestCase, Submission

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'category')
    inlines = [TestCaseInline]

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'status', 'submitted_at')
    readonly_fields = ('submitted_at',)