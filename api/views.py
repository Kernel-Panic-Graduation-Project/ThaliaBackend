import time
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from api.models import StoryJob
from api.tasks import add_job_to_queue
from .serializers import UserSerializer, LoginSerializer
from django.contrib.auth.models import User
from text_generation.generate_text import generate_text


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
        
        # Create a new job
        job = StoryJob.objects.create(
            user=request.user,
            title=story_title,
            description=story_description,
        )
        
        # Add job to queue
        add_job_to_queue(job)
        
        time.sleep(0.1)
        job.refresh_from_db()
        
        return Response({
            'job_id': job.id,
            'status': job.status,
            'position': job.position
        }, status=status.HTTP_201_CREATED)



class StoryJobStatusView(APIView):
    """
    API endpoint for checking story job status
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, job_id):
        try:
            job = StoryJob.objects.get(id=job_id, user=request.user)
            
            response_data = {
                'job_id': job.id,
                'status': job.status,
                'title': job.title,
                'position': job.position if job.status == 'queued' else 0,
            }
            
            # Include result if job is completed
            if job.status == 'completed' and job.result:
                response_data['result'] = job.result
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except StoryJob.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)


class UserJobsView(APIView):
    """
    API endpoint for listing all jobs for the current user
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        jobs = StoryJob.objects.filter(user=request.user)
        
        job_list = [{
            'job_id': job.id,
            'title': job.title,
            'status': job.status,
            'position': job.position if job.status == 'queued' else 0,
            'created_at': job.created_at,
        } for job in jobs]
        
        return Response(job_list, status=status.HTTP_200_OK)
