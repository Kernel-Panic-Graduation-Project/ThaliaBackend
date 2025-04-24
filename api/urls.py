from django.urls import path
from .views import (
    CreateStoryView, SignupView, LoginView, LogoutView,
    UserStoriesView, StoryDetailView, ChangePasswordView,
    ChangeEmailView, RequestPasswordResetView, ConfirmPasswordResetView,
    LikeStoryView, UnlikeStoryView, StoryThemesView, StoryCharactersView
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('change-email/', ChangeEmailView.as_view(), name='change-email'),
    path('request-password-reset/', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('confirm-password-reset/', ConfirmPasswordResetView.as_view(), name='confirm-password-reset'),
    
    path('create-story/', CreateStoryView.as_view(), name='create-story'),
    path('stories/', UserStoriesView.as_view(), name='user-stories'),
    path('story/<int:story_id>/', StoryDetailView.as_view(), name='story-detail'),
    path('like-story/', LikeStoryView.as_view(), name='like-story'),
    path('unlike-story/', UnlikeStoryView.as_view(), name='unlike-story'),
    path('story-themes/', StoryThemesView.as_view(), name='story-themes'),
    path('story-characters/', StoryCharactersView.as_view(), name='story-characters'),
]