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
            
            # Update job status to generating story
            job.status = 'generating_story'
            job.position = 0
            job.save()
            
            # Notify status change
            JobService.send_job_updates(job, send_individual=True)
            
            # Process the job
            generated_story = generate_text(
                description=job.story.user_description,
                theme=job.story.theme,
                characters=job.story.characters
            )

            # Get the title
            lines = generated_story.splitlines()
            if lines and lines[0].startswith("Title: "):
                result_title = lines[0][len("Title: "):].strip()
                generated_story = '\n'.join(lines[1:]).lstrip()
            else:
                result_title = ''

            if job.story:
                job.story.title = result_title
                job.story.save()
            
            # Get the generated text sections
            result_text_sections = generated_story.get('text_sections', [])
            
            if job.story:
                job.story.text_sections = result_text_sections
                job.story.save()

            job.status = 'generating_audio'
            job.save()

            # Notify status change
            JobService.send_job_updates(job, send_individual=True)
            
            # Generate audio from the text
            result_audios = []
            for section in result_text_sections:
                result_audio = generate_audio(section)
                result_audios.append(result_audio)
            
            # Update the associated story with the generated content and audio
            if job.story:
                job.story.audios = result_audios
                job.story.save()
            
            # Update job with result
            job.status = 'completed'
            job.save()
            
            # Notify status change after completion
            JobService.send_job_updates(job, send_individual=True)
            # Update positions for remaining jobs
            JobService.update_queue_positions()
        except Exception as e:
            job.status = 'failed'
            job.result = str(e)
            job.save()

            # Notify status change on failure
            JobService.send_job_updates(job, send_individual=True)
            # Update positions for remaining jobs
            JobService.update_queue_positions()
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
