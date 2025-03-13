from django.contrib import admin
from .models import StoryJob

# Register your models here.
@admin.register(StoryJob)
class StoryJobAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'position', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'description')
        }),
        ('Status Information', {
            'fields': ('status', 'position', 'result')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
