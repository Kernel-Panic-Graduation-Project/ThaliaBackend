from django.urls import path
from .views import (
    CreateStoryView, SignupView, LoginView, LogoutView,
    UserStoriesView, StoryDetailView
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('create-story/', CreateStoryView.as_view(), name='create-story'),
    path('stories/', UserStoriesView.as_view(), name='user-stories'),
    path('story/<int:story_id>/', StoryDetailView.as_view(), name='story-detail'),
]