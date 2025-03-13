import threading
import queue
import json
import asyncio
from .models import StoryJob
from text_generation.generate_text import generate_text
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Global queue for job processing
job_queue = queue.Queue()

# Flag to track if worker is running
worker_running = False

def notify_job_status_change(job, send_individual=True):
    """Send WebSocket notification when job status changes"""
    channel_layer = get_channel_layer()
    user_id = job.user.id
    room_group_name = f'jobs_{user_id}'
    
    # Get all jobs for this user (for the full jobs list update)
    jobs = StoryJob.objects.filter(user=job.user)
    jobs_data = [
        {
            'job_id': j.id,
            'title': j.title,
            'status': j.status,
            'position': j.position if j.status == 'queued' else 0,
            'created_at': j.created_at.isoformat(),
            'result': j.result if j.status == 'completed' else None
        } for j in jobs
    ]
    
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
        job_data = {
            'job_id': job.id,
            'title': job.title,
            'status': job.status,
            'position': job.position if job.status == 'queued' else 0,
            'created_at': job.created_at.isoformat(),
            'description': job.description,
            'result': job.result if job.status == 'completed' else None
        }
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'job_update',
                'job': job_data
            }
        )

def process_jobs():
    """Process jobs from the queue"""
    global worker_running
    
    while not job_queue.empty():
        job_id = job_queue.get()
        
        try:
            # Get the job from database
            job = StoryJob.objects.get(id=job_id)
            
            # Update job status to processing
            job.status = 'processing'
            job.position = 0
            job.save()
            
            # Notify status change
            notify_job_status_change(job)
            
            # Process the job
            result = generate_text(job.description)
            
            # Update job with result
            job.result = result
            job.status = 'completed'
            job.save()
            
            # Notify status change again
            notify_job_status_change(job)
            
            # Update positions for remaining jobs
            update_queue_positions()
            
        except Exception as e:
            try:
                job.status = 'failed'
                job.result = str(e)
                job.save()
                
                # Notify status change for failure
                notify_job_status_change(job)
            except:
                pass
        
        finally:
            job_queue.task_done()
    
    # No more jobs, worker is no longer running
    worker_running = False

def update_queue_positions():
    """Update the position of all queued jobs"""
    queued_jobs = StoryJob.objects.filter(status='queued').order_by('created_at')
    
    # Update positions
    for i, job in enumerate(queued_jobs):
        job.position = i + 1
        job.save(update_fields=['position'])
        
        # Notify position change
        notify_job_status_change(job)

def add_job_to_queue(job):
    """Add a job to the processing queue and start worker if needed"""
    global worker_running
    
    # Add job to queue
    job_queue.put(job.id)
    
    # Update queue positions
    update_queue_positions()
    
    # Start worker thread if not already running
    if not worker_running:
        worker_running = True
        thread = threading.Thread(target=process_jobs)
        thread.daemon = True
        thread.start()