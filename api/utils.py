def serialize_job(job):
    """
    Centralized function to serialize a job consistently across the application
    """
    return {
        'job_id': job.id,
        'story_id': job.story.id,
        'title': job.title,
        'status': job.status,
        'position': job.position if job.status == 'queued' else 0,
        'created_at': job.created_at.isoformat(),
        'description': job.description,
    }