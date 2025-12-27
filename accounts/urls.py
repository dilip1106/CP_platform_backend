from django.urls import path
from .views import RegisterView, UserDetailView

from django.urls import path
from .views import RegisterView, LoginView, UserDetailView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/<int:id>/', UserDetailView.as_view(), name='user_detail'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
