from django.urls import path
from .views import (
    ProblemListView, 
    ProblemDetailView, 
    SubmissionView, 
    UserSubmissionsView,
    AdminProblemCreateView,
    AdminTestCaseCreateView
)

urlpatterns = [
    # Public/User Routes
    path('problems/', ProblemListView.as_view(), name='problem-list'),
    path('problems/<int:pk>/', ProblemDetailView.as_view(), name='problem-detail'),
    path('submit/', SubmissionView.as_view(), name='submit-code'),
    path('my-submissions/', UserSubmissionsView.as_view(), name='user-submissions'),
    
    # Admin Routes
    path('admin/problems/create/', AdminProblemCreateView.as_view(), name='admin-problem-create'),
    path('admin/test-cases/create/', AdminTestCaseCreateView.as_view(), name='admin-testcase-create'),
]