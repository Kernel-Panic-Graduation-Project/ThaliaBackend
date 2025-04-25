from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from .models import StoryJob, Story, StoryTheme, StoryCharacter, StoryCharacterSource

admin.site.site_header = "Thalia Administration"
admin.site.site_title = "Thalia Admin Portal"

# Register your models here.
@admin.register(StoryJob)
class StoryJobAdmin(admin.ModelAdmin):
    list_display = ('story__title', 'get_user', 'status', 'position', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('story__title', 'story__user_description', 'story__user__username',)
    readonly_fields = ('created_at', 'updated_at', 'get_story_title', 'get_story_description', 'get_user')
    fieldsets = (
        (None, {
            'fields': ('story',)
        }),
        ('Story Details', {
            'fields': ('get_story_title', 'get_story_description', 'get_user')
        }),
        ('Status Information', {
            'fields': ('status', 'position', 'result'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def get_story_title(self, obj):
        return obj.story.title if obj.story else 'No Story'
    get_story_title.short_description = 'Story Title'
    get_story_title.admin_order_field = 'story__title'
    
    def get_story_description(self, obj):
        return obj.story.user_description if obj.story else 'No Description'
    get_story_description.short_description = 'Story Description'
    get_story_description.admin_order_field = 'story__user_description'

    def get_user(self, obj):
        return obj.story.user if obj.story else None
    get_user.short_description = 'User'
    get_user.admin_order_field = 'story__user__username'

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'user_description', 'theme', 'characters', 'text_sections', 'audios', 'user__username')
    readonly_fields = ('created_at', 'text_sections', 'audios')
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'user_description', 'theme', 'characters', 'text_sections', 'audios')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )

@admin.register(StoryCharacter)
class StoryCharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'source', 'image_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'user', 'source')
    readonly_fields = ('created_at', 'image_preview')
    fieldsets = (
        (None, {
            'fields': ('name', 'user', 'source', 'image', 'image_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="150" />')
        return "No Image"
    image_preview.short_description = 'Image Preview'

# Define an inline admin for the liked stories
class LikedStoriesInline(admin.TabularInline):
    model = Story.likes.through
    verbose_name = "Liked Story"
    verbose_name_plural = "Liked Stories"
    extra = 0
    readonly_fields = ('story_title', 'story_created_at')
    fields = ('story_title', 'story_created_at')
    can_delete = False

    def story_title(self, obj):
        return obj.story.title
    story_title.short_description = 'Story Title'

    def story_created_at(self, obj):
        return obj.story.created_at
    story_created_at.short_description = 'Created At'

    def has_add_permission(self, request, obj=None):
        return False

# Define a new UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (LikedStoriesInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(StoryTheme)
admin.site.register(StoryCharacterSource)