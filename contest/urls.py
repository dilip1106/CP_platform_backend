from django.urls import path
from .views import (
    ContestListView,
    ContestDetailView,
    ContestCreateView,
    ContestAddManagerView,
    ContestAddProblemView,
    ContestJoinView,
    ContestProblemListView,
    ContestProblemDetailView,
    ContestLeaderboardView,
)

urlpatterns = [
    # -------------------------
    # Contests
    # -------------------------
    path(
        "contests/",
        ContestListView.as_view(),
        name="contest-list"
    ),

    path(
        "contests/create/",
        ContestCreateView.as_view(),
        name="contest-create"
    ),

    path(
        "contests/<slug:slug>/",
        ContestDetailView.as_view(),
        name="contest-detail"
    ),

    path(
        "contests/<int:contest_id>/join/",
        ContestJoinView.as_view(),
        name="contest-join"
    ),

    path(
        "contests/<int:contest_id>/add-manager/",
        ContestAddManagerView.as_view(),
        name="contest-add-manager"
    ),

    path(
        "contests/<int:contest_id>/add-problem/",
        ContestAddProblemView.as_view(),
        name="contest-add-problem"
    ),

    # -------------------------
    # Contest Problems
    # -------------------------
    path(
        "contests/<slug:slug>/problems/",
        ContestProblemListView.as_view(),
        name="contest-problem-list"
    ),

    path(
        "contests/<slug:contest_slug>/problems/<slug:problem_slug>/",
        ContestProblemDetailView.as_view(),
        name="contest-problem-detail"
    ),
    path('contests/<slug:contest_slug>/leaderboard/', ContestLeaderboardView.as_view(), name='contest-leaderboard'),
]
