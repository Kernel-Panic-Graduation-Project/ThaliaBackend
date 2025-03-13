import threading
import queue

from story_generation.generate_audio import generate_audio
from .models import StoryJob
from story_generation.generate_text import generate_text
from .services import JobService

# Global queue for job processing
job_queue = queue.Queue()

# Flag to track if worker is running
worker_running = False

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
            JobService.send_job_updates(job, send_individual=True)
            
            # Process the job
            result_text = generate_text(job.description)
            
            # Generate audio from the text
            result_audio = generate_audio(result_text)
            
            # Update job with result - include both text and audio
            job.status = 'completed'
            job.save()
            
            # Update the associated story with the generated content and audio
            if job.story:
                job.story.content = result_text
                job.story.audio_data = result_audio
                job.story.save()
            
            # Notify status change again
            JobService.send_job_updates(job, send_individual=True)
            
            # Update positions for remaining jobs
            JobService.update_queue_positions()
            
        except Exception as e:
            try:
                job.status = 'failed'
                job.result = str(e)
                job.save()
                
                # Notify status change for failure
                JobService.send_job_updates(job, send_individual=True)
            except:
                pass
        
        finally:
            job_queue.task_done()
    
    # No more jobs, worker is no longer running
    worker_running = False

def add_job_to_queue(job):
    """Add a job to the processing queue and start worker if needed"""
    global worker_running
    
    # Add job to queue
    job_queue.put(job.id)
    
    # Update queue positions
    JobService.update_queue_positions()
    
    # Start worker thread if not already running
    if not worker_running:
        worker_running = True
        thread = threading.Thread(target=process_jobs)
        thread.daemon = True
        thread.start()
