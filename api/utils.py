from profanity_check import predict

def serialize_job(job):
    """
    Centralized function to serialize a job consistently across the application
    """
    return {
        'job_id': job.id,
        'story_id': job.story.id,
        'title': job.story.title if job.story else 'Untitled Story',
        'status': job.status,
        'position': job.position if job.status == 'queued' else 0,
        'created_at': job.created_at.isoformat(),
        'description': job.story.user_description if job.story else '',
        'favorited': job.user in job.story.likes.all() if job.story else False,
    }

def contains_profanity(text):
    """
    Check if the text contains profanity
    """
    prediction = predict([text])[0]
    
    return prediction