import time
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from api.models import StoryJob, Story
from api.tasks import add_job_to_queue
from api.utils import contains_profanity
from .serializers import UserSerializer, LoginSerializer
from django.contrib.auth.models import User
from .models import PasswordResetToken


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


class ChangePasswordView(APIView):
    """
    API endpoint for changing user password
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)


class ChangeEmailView(APIView):
    """
    API endpoint for changing user email
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_email = request.data.get('new_email')
        
        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=new_email).exists():
            return Response({'error': 'Email already in use.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.email = new_email
        user.save()
        
        return Response({'message': 'Email changed successfully.'}, status=status.HTTP_200_OK)


class CreateStoryView(APIView):
    """
    API endpoint for creating a story job
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        story_description = request.data.get('description')

        if contains_profanity(story_description):
            return Response({
                'error': 'Profanity detected in request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not story_description:
            return Response({
                'error': 'Description is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        story = Story.objects.create(
            user=request.user,
            user_description=story_description,
        )
        
        # Create a new job and link it to the story
        job = StoryJob.objects.create(
            user=request.user,
            title='Untitled Story',
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
                'text_sections': story.get_text_sections(),
                'audios': story.get_audios(),
                'created_at': story.created_at,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Story.DoesNotExist:
            return Response({'error': 'Story not found'}, status=status.HTTP_404_NOT_FOUND)


class RequestPasswordResetView(APIView):
    """
    API endpoint to request a password reset
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether a user exists for security
            return Response({'message': 'If an account with this email exists, a reset code has been sent.'}, 
                           status=status.HTTP_200_OK)
        
        # Invalidate any existing tokens
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Create new token
        reset_token = PasswordResetToken(user=user)
        reset_token.save()
        
        # Send email with the token
        subject = 'Thalia Password Reset Code'
        message = f'Your password reset code is: {reset_token.token}\nIt will expire in 1 hour.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        
        send_mail(subject, message, from_email, recipient_list)
        
        return Response({'message': 'If an account with this email exists, a reset code has been sent.'}, 
                       status=status.HTTP_200_OK)


class ConfirmPasswordResetView(APIView):
    """
    API endpoint to confirm password reset with token
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')
        
        if not all([email, code, new_password]):
            return Response({'error': 'Email, token and new password are required.'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid email or token.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reset_token = PasswordResetToken.objects.get(user=user, token=code, is_used=False)
            
            if not reset_token.is_valid():
                return Response({'error': 'Token has expired.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'Invalid email or token.'}, status=status.HTTP_400_BAD_REQUEST)
