from django.contrib import admin
from .models import Challenge, ChallengeTestCase, PracticeProblem, PracticeProblemTestCase
from problems.models import Tag
from contest.models import ContestItem


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

@admin.register(ContestItem)
class ContestItemAdmin(admin.ModelAdmin):
    list_display = ['contest', 'get_item_name', 'order', 'score', 'get_item_type']
    list_filter = ['contest']  # remove 'item_type'
    search_fields = ['problem__title', 'challenge__title']

    def get_item_name(self, obj):
        return obj.get_item().title
    get_item_name.short_description = "Item"

    def get_item_type(self, obj):
        return obj.item_type
    get_item_type.short_description = "Item Type"
