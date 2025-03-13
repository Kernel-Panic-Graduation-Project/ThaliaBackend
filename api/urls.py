from django.urls import path
from .views import (
    CreateStoryView, SignupView, LoginView, LogoutView,
    StoryJobStatusView, UserJobsView
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('create-story/', CreateStoryView.as_view(), name='create-story'),
    path('job/<int:job_id>/', StoryJobStatusView.as_view(), name='job-status'),
    path('jobs/', UserJobsView.as_view(), name='user-jobs'),
]