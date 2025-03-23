from django.db import models
from django.contrib.auth.models import User
import json

# Create your models here.
class StoryJob(models.Model):
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    position = models.IntegerField(default=0)
    story = models.ForeignKey('Story', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username}'s job: {self.title} ({self.status})"


class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    user_description = models.TextField(blank=True, null=True)
    text_sections = models.TextField(blank=True, null=True)  # Stored as JSON
    audios = models.TextField(blank=True, null=True)  # Stored as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_text_sections(self):
        """Return text sections as a list"""
        return json.loads(self.text_sections) if self.text_sections else []
    
    def set_text_sections(self, sections_list):
        """Set text sections from a list"""
        self.text_sections = json.dumps(sections_list)
        
    def get_audios(self):
        """Return audios as a list"""
        return json.loads(self.audios) if self.audios else []
    
    def set_audios(self, audios_list):
        """Set audios from a list"""
        self.audios = json.dumps(audios_list)
    
    def __str__(self):
        return self.title