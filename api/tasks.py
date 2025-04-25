import threading
import queue
import traceback
from story_generation.generate_text import generate_text
from story_generation.generate_audio import generate_audio
from story_generation.generate_image import generate_images, generate_images_gemini, generate_sections_and_image_prompts, split_and_generate_image_prompts
from .models import StoryJob
from .services import JobService
import base64

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
                
            # Update job status to generating image
            job.status = 'generating_image'
            job.save()

            # Notify status change
            JobService.send_job_updates(job, send_individual=True)
            
            # Get the generated sections and image prompts
            divide_by_ai = True
            if divide_by_ai:
                sections = generate_sections_and_image_prompts(generated_story, theme=job.story.theme)
            else:
                sections = split_and_generate_image_prompts(generated_story)
            model_category = job.story.characters[0].get('source', '')
            sections = generate_images(sections, model_category)

            story_text_sections = []
            story_images = []
            for section in sections:
                story_text_sections.append(section.get('text', ''))
                # Convert binary image data to base64 string for JSON serialization
                image_data = section.get('image')
                if image_data and isinstance(image_data, bytes):
                    encoded_image = base64.b64encode(image_data).decode('utf-8')
                else:
                    encoded_image = None

                story_images.append({
                    'image': encoded_image,
                    'image_mime_type': section.get('image_mime_type', None),
                })

            if job.story:
                job.story.text_sections = story_text_sections
                job.story.images = story_images
                job.story.save()

            job.status = 'generating_audio'
            job.save()

            # Notify status change
            JobService.send_job_updates(job, send_individual=True)

            # Generate audio from the text
            result_audios = []
            for section in story_text_sections:
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
            job.result = str(e) + "\n" + traceback.format_exc()
            job.position = 0
            job.save()

            # Notify status change on failure
            JobService.send_job_updates(job, send_individual=True)
            # Update positions for remaining jobs
            JobService.update_queue_positions()
            raise e
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
