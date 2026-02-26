"""
Django Admin configuration for Onboarding_AI Knowledge Base
"""

from django.contrib import admin
from .models import (
    GitCommit, 
    GitCommitFile, 
    Meeting, 
    JiraTicket, 
    ConfluencePage,
    EntityReference,
    Project,
    ProjectEntity
)


@admin.register(GitCommit)
class GitCommitAdmin(admin.ModelAdmin):
    list_display = ['sha_short', 'author_name', 'commit_date', 'message_short', 'related_tickets']
    list_filter = ['author_name', 'commit_date']
    search_fields = ['sha', 'message', 'author_name', 'author_email']
    
    def sha_short(self, obj):
        return obj.sha[:7]
    sha_short.short_description = 'SHA'
    
    def message_short(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 else obj.message
    message_short.short_description = 'Message'


@admin.register(GitCommitFile)
class GitCommitFileAdmin(admin.ModelAdmin):
    list_display = ['filename', 'commit', 'status', 'additions', 'deletions']
    list_filter = ['status']
    search_fields = ['filename']


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'meeting_date', 'source_filename']
    search_fields = ['title', 'summary', 'raw_vtt_content']


@admin.register(JiraTicket)
class JiraTicketAdmin(admin.ModelAdmin):
    list_display = ['issue_key', 'issue_type', 'summary', 'status', 'assignee', 'priority']
    list_filter = ['status', 'issue_type', 'priority', 'assignee']
    search_fields = ['issue_key', 'summary', 'description']


@admin.register(ConfluencePage)
class ConfluencePageAdmin(admin.ModelAdmin):
    list_display = ['title', 'space', 'author', 'version', 'page_updated_date']
    list_filter = ['space', 'author']
    search_fields = ['title', 'content']


@admin.register(EntityReference)
class EntityReferenceAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'source_id', 'reference_type', 'reference_id', 'extraction_method']
    list_filter = ['source_type', 'reference_type', 'extraction_method']
    search_fields = ['reference_id']
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'epic_key', 'github_repo', 'owner', 'start_date']
    list_filter = ['status']
    search_fields = ['name', 'description', 'epic_key', 'github_repo']


@admin.register(ProjectEntity)
class ProjectEntityAdmin(admin.ModelAdmin):
    list_display = ['project', 'entity_type', 'entity_id', 'added_manually']
    list_filter = ['entity_type', 'added_manually']