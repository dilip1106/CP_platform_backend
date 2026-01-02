from django.contrib import admin
from .models import Challenge, ChallengeTestCase, PracticeProblem, PracticeProblemTestCase, Tag, ContestChallenge


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'difficulty', 'created_by', 'allow_public_practice_after_contest', 'created_at']
    list_filter = ['difficulty', 'created_at', 'allow_public_practice_after_contest']
    search_fields = ['title', 'slug']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['tags']


@admin.register(ChallengeTestCase)
class ChallengeTestCaseAdmin(admin.ModelAdmin):
    list_display = ['challenge', 'is_sample', 'is_hidden']
    list_filter = ['is_sample', 'is_hidden']
    search_fields = ['challenge__title']


@admin.register(PracticeProblem)
class PracticeProblemAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'difficulty', 'created_by', 'created_at']
    list_filter = ['difficulty', 'created_at']
    search_fields = ['title', 'slug']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['tags']


@admin.register(PracticeProblemTestCase)
class PracticeProblemTestCaseAdmin(admin.ModelAdmin):
    list_display = ['problem', 'is_sample']
    list_filter = ['is_sample']
    search_fields = ['problem__title']


@admin.register(ContestChallenge)
class ContestChallengeAdmin(admin.ModelAdmin):
    list_display = ['contest', 'challenge', 'order', 'score', 'time_limit']
    list_filter = ['contest', 'order']
    search_fields = ['challenge__title', 'contest__title']
