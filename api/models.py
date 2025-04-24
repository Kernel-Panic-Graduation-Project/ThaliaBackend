from django.db import models
from django.contrib.auth.models import User
import json
from django.utils import timezone
from datetime import timedelta
import random

# Create your models here.
class StoryJob(models.Model):
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('generating_story', 'Generating Story'),
        ('generating_audio', 'Generating Audio'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    result = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    position = models.IntegerField(default=0)
    story = models.ForeignKey('Story', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.story.user.username}'s job: {self.story.title} ({self.status})"


class Story(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    user_description = models.TextField(blank=True, null=True)
    theme = models.CharField(max_length=100, blank=True, null=True)
    characters = models.JSONField(blank=True, null=True)
    text_sections = models.JSONField(blank=True, null=True)
    audios = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_stories', blank=True)
    
    def get_likes_count(self):
        """Return the number of likes for the story"""
        return self.likes.count()
    
    def __str__(self):
        return self.title


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.token:
            # Generate a 6-digit code
            self.token = str(random.randint(100000, 999999))
        
        if not self.expires_at:
            # Set expiration to 1 hour from creation
            self.expires_at = timezone.now() + timedelta(hours=1)
            
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()


class StoryCharacterSource(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    def __str__(self):
        return self.name


class StoryCharacter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=100)
    source = models.ForeignKey(StoryCharacterSource, on_delete=models.CASCADE, blank=True, null=True)
    image = models.ImageField(upload_to='story_characters/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    def __str__(self):
        return self.name + (" (" + str(self.source) + ")") if self.source else ""


class StoryTheme(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.name
