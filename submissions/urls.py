from django.urls import path
from .views import SubmissionCreateView, UserSubmissionListView,SubmitSolutionView

urlpatterns = [
    path('', SubmissionCreateView.as_view(), name='submit'),
    path('me/', UserSubmissionListView.as_view(), name='my-submissions'),
    path('submit/', SubmitSolutionView.as_view(), name='submit_solution'),
]

