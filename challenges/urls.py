from django.urls import path
from .views import (
    ChallengeCreateView,
    ChallengeListView,
    ChallengeDetailView,
    ChallengeTestCaseCreateView,
    PublicPracticeChallengesView,
    PublicPracticeChallengeDetailView,
    PracticeProblemCreateView,
    PracticeProblemListView,
    PracticeProblemDetailView,
    PracticeProblemTestCaseCreateView,
)

urlpatterns = [
    # ========================
    # Manager Challenge APIs
    # ========================
    path(
        'challenges/',
        ChallengeCreateView.as_view(),
        name='challenge-create'
    ),
    path(
        'challenges/me/',
        ChallengeListView.as_view(),
        name='challenge-list'
    ),
    path(
        'challenges/<int:challenge_id>/',
        ChallengeDetailView.as_view(),
        name='challenge-detail'
    ),
    path(
        'challenges/<int:challenge_id>/test-cases/',
        ChallengeTestCaseCreateView.as_view(),
        name='challenge-test-case-create'
    ),

    # ========================
    # Public Practice Challenges
    # ========================
    path(
        'practice/challenges/',
        PublicPracticeChallengesView.as_view(),
        name='public-practice-challenges'
    ),
    path(
        'practice/challenges/<slug:slug>/',
        PublicPracticeChallengeDetailView.as_view(),
        name='public-practice-challenge-detail'
    ),

    # ========================
    # Superuser Practice Problems
    # ========================
    path(
        'practice/problems/',
        PracticeProblemListView.as_view(),
        name='practice-problem-list'
    ),
    path(
        'practice/problems/create/',
        PracticeProblemCreateView.as_view(),
        name='practice-problem-create'
    ),
    path(
        'practice/problems/<int:problem_id>/',
        PracticeProblemDetailView.as_view(),
        name='practice-problem-detail'
    ),
    path(
        'practice/problems/<int:problem_id>/test-cases/',
        PracticeProblemTestCaseCreateView.as_view(),
        name='practice-problem-test-case-create'
    ),
]
