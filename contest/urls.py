from django.urls import path
from .views import (
    ContestListView,
    ContestDetailView,
    ContestDetailWithRegistrationView,
    ContestCreateView,
    ContestAddManagerView,
    RemoveContestManagerView,
    ContestAddItemView,  # NEW: Unified endpoint
    ContestAddProblemView,  # DEPRECATED: For backward compatibility
    RemoveContestItemView,  # NEW: Unified endpoint
    RemoveContestProblemView,  # DEPRECATED: For backward compatibility
    ContestRegisterView,
    ContestUnregisterView,
    ContestRegistrationStatusView,
    ContestRegistrationsListView,
    UserRegisteredContestsView,
    ContestProblemListView,
    ContestItemDetailView,  # NEW: Unified endpoint
    ContestProblemDetailView,  # DEPRECATED: For backward compatibility
    ContestLeaderboardView,
    ContestSubmissionCreateView,
    ContestStatusView,
    ContestLeaveView,
    ContestUpdateView,
    UserSubmissionsView,
    SubmissionDetailView,
    UserContestStatsView,
    ContestSearchView,
    ContestListWithStatusView,
    ContestJoinView,
    ContestPublishView,
    ManagerContestSubmissionsView,
    ManagerViewSubmissionCodeView,
    ManagerContestLeaderboardView,
    ManagerSubmissionAnalyticsView,
    ManagerExportContestDataView,
)

urlpatterns = [
    # -------------------------
    # Contests - Main CRUD
    # -------------------------
    path(
        "contests/",
        ContestListView.as_view(),
        name="contest-list"
    ),

    path(
        "contests/with-status/",
        ContestListWithStatusView.as_view(),
        name="contest-list-with-status"
    ),

    path(
        "contests/search/",
        ContestSearchView.as_view(),
        name="contest-search"
    ),

    path(
        "contests/my-registrations/",
        UserRegisteredContestsView.as_view(),
        name="user-registered-contests"
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
        "contests/<slug:slug>/with-registration/",
        ContestDetailWithRegistrationView.as_view(),
        name="contest-detail-with-registration"
    ),

    path(
        "contests/<slug:slug>/status/",
        ContestStatusView.as_view(),
        name="contest-status"
    ),

    path(
        "contests/<int:contest_id>/update/",
        ContestUpdateView.as_view(),
        name="contest-update"
    ),

    # -------------------------
    # Contest Registration
    # -------------------------
    path(
        "contests/<int:contest_id>/register/",
        ContestRegisterView.as_view(),
        name="contest-register"
    ),

    path(
        "contests/<int:contest_id>/unregister/",
        ContestUnregisterView.as_view(),
        name="contest-unregister"
    ),

    path(
        "contests/<int:contest_id>/registration-status/",
        ContestRegistrationStatusView.as_view(),
        name="contest-registration-status"
    ),

    path(
        "contests/<int:contest_id>/registrations/",
        ContestRegistrationsListView.as_view(),
        name="contest-registrations-list"
    ),

    # -------------------------
    # Contest Participation
    # -------------------------
    path(
        "contests/<int:contest_id>/join/",
        ContestJoinView.as_view(),
        name="contest-join"
    ),

    path(
        "contests/<int:contest_id>/leave/",
        ContestLeaveView.as_view(),
        name="contest-leave"
    ),

    # -------------------------
    # Contest Management
    # -------------------------
    path(
        "contests/<int:contest_id>/add-manager/",
        ContestAddManagerView.as_view(),
        name="contest-add-manager"
    ),

    path(
        "contests/<int:contest_id>/remove-manager/",
        RemoveContestManagerView.as_view(),
        name="contest-remove-manager"
    ),

    # NEW: Unified endpoint for adding items
    path(
        "contests/<int:contest_id>/add-item/",
        ContestAddItemView.as_view(),
        name="contest-add-item"
    ),

    # DEPRECATED: For backward compatibility
    path(
        "contests/<int:contest_id>/add-problem/",
        ContestAddProblemView.as_view(),
        name="contest-add-problem"
    ),

    # NEW: Unified endpoint for removing items
    path(
        "contests/<int:contest_id>/remove-item/<int:item_id>/",
        RemoveContestItemView.as_view(),
        name="contest-remove-item"
    ),

    # DEPRECATED: For backward compatibility
    path(
        "contests/<int:contest_id>/remove-problem/<int:problem_id>/",
        RemoveContestProblemView.as_view(),
        name="contest-remove-problem"
    ),

    # -------------------------
    # Contest Items (Problems + Challenges)
    # -------------------------
    path(
        "contests/<slug:slug>/items/",
        ContestProblemListView.as_view(),
        name="contest-item-list"
    ),

    # NEW: Unified endpoint
    path(
        "contests/<slug:contest_slug>/items/<slug:item_slug>/",
        ContestItemDetailView.as_view(),
        name="contest-item-detail"
    ),

    # DEPRECATED: For backward compatibility
    path(
        "contests/<slug:contest_slug>/problems/<slug:problem_slug>/",
        ContestProblemDetailView.as_view(),
        name="contest-problem-detail"
    ),

    # -------------------------
    # Submissions
    # -------------------------
    path(
        "contests/<slug:contest_slug>/problems/<slug:problem_slug>/submit/",
        ContestSubmissionCreateView.as_view(),
        name="contest-submit-solution"
    ),

    path(
        "contests/<slug:contest_slug>/problems/<slug:problem_slug>/submissions/",
        UserSubmissionsView.as_view(),
        name="user-submissions"
    ),

    path(
        "submissions/<int:submission_id>/",
        SubmissionDetailView.as_view(),
        name="submission-detail"
    ),

    # -------------------------
    # Contest Stats & Leaderboard
    # -------------------------
    path(
        "contests/<slug:slug>/my-stats/",
        UserContestStatsView.as_view(),
        name="user-contest-stats"
    ),

    path(
        "contests/<slug:contest_slug>/leaderboard/",
        ContestLeaderboardView.as_view(),
        name="contest-leaderboard"
    ),

    # -------------------------
    # Manager Views
    # -------------------------
    path(
        "contests/<int:contest_id>/manager/submissions/",
        ManagerContestSubmissionsView.as_view(),
        name="manager-contest-submissions"
    ),

    path(
        "contests/<int:contest_id>/manager/submissions/<int:submission_id>/code/",
        ManagerViewSubmissionCodeView.as_view(),
        name="manager-view-submission-code"
    ),

    path(
        "contests/<int:contest_id>/manager/leaderboard/",
        ManagerContestLeaderboardView.as_view(),
        name="manager-contest-leaderboard"
    ),

    path(
        "contests/<int:contest_id>/manager/analytics/",
        ManagerSubmissionAnalyticsView.as_view(),
        name="manager-submission-analytics"
    ),

    path(
        "contests/<int:contest_id>/manager/export/",
        ManagerExportContestDataView.as_view(),
        name="manager-export-data"
    ),

    # Publish contest (DRAFT → SCHEDULED)
    path(
        "contests/<int:contest_id>/publish/",
        ContestPublishView.as_view(),
        name="contest-publish"
    ),
]
