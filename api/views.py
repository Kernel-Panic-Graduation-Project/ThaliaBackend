import time
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from api.models import StoryJob, Story
from api.tasks import add_job_to_queue
from .serializers import UserSerializer, LoginSerializer
from django.contrib.auth.models import User


# Create your views here.
class LoginView(APIView):
    """
    API endpoint for user login using email
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    token, created = Token.objects.get_or_create(user=user)
                    return Response({
                        'token': token.key,
                        'user_id': user.pk,
                        'username': user.username,
                        'email': user.email
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({'error': 'No user with this email exists'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignupView(generics.CreateAPIView):
    """
    API endpoint for user signup
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    API endpoint for user logout
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateStoryView(APIView):
    """
    API endpoint for creating a story job
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        story_title = request.data.get('title')
        story_description = request.data.get('description')
        
        if not story_title or not story_description:
            return Response({
                'error': 'Title and description are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        story = Story.objects.create(
            user=request.user,
            title=story_title,
            user_description=story_description,
            content=""
        )
        
        # Create a new job and link it to the story
        job = StoryJob.objects.create(
            user=request.user,
            title=story_title,
            description=story_description,
            story=story
        )
        
        # Add job to queue
        add_job_to_queue(job)
        
        time.sleep(0.1)
        job.refresh_from_db()
        
        return Response({
            'job_id': job.id,
            'story_id': story.id,
            'status': job.status,
            'position': job.position
        }, status=status.HTTP_201_CREATED)


class UserStoriesView(APIView):
    """
    API endpoint for listing all stories for the current user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        stories = Story.objects.filter(user=request.user)
        
        story_list = [{
            'story_id': story.id,
            'title': story.title,
            'content': story.content,
            'created_at': story.created_at,
        } for story in stories]
        
        return Response(story_list, status=status.HTTP_200_OK)


class StoryDetailView(APIView):
    """
    API endpoint for retrieving a specific story
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, story_id):
        try:
            story = Story.objects.get(id=story_id, user=request.user)
            
            response_data = {
                'story_id': story.id,
                'title': story.title,
                'user_description': story.user_description,
                'content': story.content,
                'audio_data': story.audio_data,
                'created_at': story.created_at,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Story.DoesNotExist:
            return Response({'error': 'Story not found'}, status=status.HTTP_404_NOT_FOUND)