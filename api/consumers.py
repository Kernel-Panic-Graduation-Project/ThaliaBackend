import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

from api.models import StoryJob
from .services import JobService
from .utils import serialize_job

class JobConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'jobs_{self.user_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the connection
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')
        
        # Process the message based on its type
        await self.process_message(action, text_data_json)

    # Process different message types
    async def process_message(self, action, data):
        if action == 'fetch_stories':
            # Fetch all jobs for the user
            jobs = await self.get_user_jobs()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'jobs_update',
                    'jobs': jobs
                }
            )
        elif action == 'fetch_job':
            # Fetch a specific job
            job_id = data.get('job_id')
            if job_id:
                job = await self.get_single_job(job_id)
                if job:
                    await self.send(text_data=json.dumps({
                        'job': job
                    }))

    # Receive message from room group
    async def jobs_update(self, event):
        jobs = event['jobs']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'jobs': jobs
        }))

    async def job_update(self, event):
        """Handle individual job updates"""
        job = event['job']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'job': job
        }))

    @database_sync_to_async
    def get_user_jobs(self):
        try:
            user = User.objects.get(id=self.user_id)
            jobs = JobService.get_jobs_for_user(user)
            return [serialize_job(job) for job in jobs]
        except User.DoesNotExist:
            return []

    @database_sync_to_async
    def get_single_job(self, job_id):
        try:
            user = User.objects.get(id=self.user_id)
            job = JobService.get_job_by_id(job_id, user)
            return serialize_job(job)
        except (User.DoesNotExist, StoryJob.DoesNotExist):
            return None