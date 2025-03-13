from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import StoryJob
from .utils import serialize_job

class JobService:
    """Service class for job-related operations"""
    
    @staticmethod
    def get_jobs_for_user(user):
        """Get all jobs for a user"""
        return StoryJob.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def get_job_by_id(job_id, user=None):
        """Get a specific job by ID, optionally filtering by user"""
        query = {'id': job_id}
        if user:
            query['user'] = user
        return StoryJob.objects.get(**query)
    
    @staticmethod
    def update_queue_positions():
        """Update the position of all queued jobs"""
        queued_jobs = StoryJob.objects.filter(status='queued').order_by('created_at')
        
        # Update positions
        for i, job in enumerate(queued_jobs):
            job.position = i + 1
            job.save(update_fields=['position'])
    
    @staticmethod
    def send_job_updates(job, send_individual=True):
        """Send WebSocket notifications about job status changes"""
        channel_layer = get_channel_layer()
        user_id = job.user.id
        room_group_name = f'jobs_{user_id}'
        
        # Get all jobs for this user
        jobs = JobService.get_jobs_for_user(job.user)
        jobs_data = [serialize_job(j) for j in jobs]
        
        # Send full jobs list update
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'jobs_update',
                'jobs': jobs_data
            }
        )
        
        # Send individual job update
        if send_individual:
            job_data = serialize_job(job)
            
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'job_update',
                    'job': job_data
                }
            )