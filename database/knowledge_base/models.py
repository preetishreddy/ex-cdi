"""
Django Models for Onboarding_AI Knowledge Base

These models map to the existing PostgreSQL tables.
Using managed = False since tables already exist.
"""

import uuid
import re
from django.db import models
from django.contrib.postgres.fields import ArrayField


class GitCommit(models.Model):
    """Stores git commit information"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sha = models.CharField(max_length=40, unique=True)
    author_name = models.CharField(max_length=255)
    author_email = models.EmailField(max_length=255)
    commit_date = models.DateTimeField()
    message = models.TextField()
    related_tickets = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'git_commits'
        managed = False  # Table already exists
        ordering = ['-commit_date']
    
    def __str__(self):
        return f"{self.sha[:7]} - {self.message[:50]}"
    
    def extract_ticket_references(self):
        """Extract Jira ticket references from commit message"""
        pattern = r'PAY-\d+'
        matches = re.findall(pattern, self.message, re.IGNORECASE)
        return list(set([m.upper() for m in matches]))


class GitCommitFile(models.Model):
    """Stores files changed in each commit"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commit = models.ForeignKey(
        GitCommit, 
        on_delete=models.CASCADE, 
        related_name='files',
        db_column='commit_id'
    )
    filename = models.CharField(max_length=500)
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'git_commit_files'
        managed = False
    
    def __str__(self):
        return f"{self.filename} ({self.status})"


class Meeting(models.Model):
    """Stores meeting metadata and processed content"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500, blank=True, null=True)
    meeting_date = models.DateTimeField(blank=True, null=True)
    raw_vtt_content = models.TextField()
    summary = models.TextField(blank=True, null=True)
    key_decisions = models.TextField(blank=True, null=True)
    action_items = models.TextField(blank=True, null=True)
    participants = models.TextField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    source_filename = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'meetings'
        managed = False
        ordering = ['-meeting_date']
    
    def __str__(self):
        return self.title or f"Meeting {self.id}"
    
    def extract_participants_from_vtt(self):
        """Extract unique speaker names from VTT content"""
        pattern = r'^([A-Za-z\s\']+):'
        lines = self.raw_vtt_content.split('\n')
        speakers = set()
        for line in lines:
            match = re.match(pattern, line.strip())
            if match:
                speaker = match.group(1).strip()
                if not re.match(r'^\d', speaker):
                    speakers.add(speaker)
        return list(speakers)
    
    def extract_ticket_references(self):
        """Extract Jira ticket references from transcript"""
        pattern = r'PAY-\d+'
        matches = re.findall(pattern, self.raw_vtt_content, re.IGNORECASE)
        return list(set([m.upper() for m in matches]))


class JiraTicket(models.Model):
    """Stores Jira ticket information (flat structure)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue_key = models.CharField(max_length=50, unique=True)
    issue_type = models.CharField(max_length=50)
    summary = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=50, blank=True, null=True)
    assignee = models.CharField(max_length=255, blank=True, null=True)
    reporter = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    resolved_date = models.DateTimeField(blank=True, null=True)
    labels = models.TextField(blank=True, null=True)
    epic_link = models.CharField(max_length=50, blank=True, null=True)
    sprint = models.CharField(max_length=100, blank=True, null=True)
    story_points = models.IntegerField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'jira_tickets'
        managed = False
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.issue_key}: {self.summary[:50]}"


class ConfluencePage(models.Model):
    """Stores Confluence page content and metadata"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    space = models.CharField(max_length=255, blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    labels = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list
    )
    version = models.IntegerField(default=1)
    page_created_date = models.DateTimeField(blank=True, null=True)
    page_updated_date = models.DateTimeField(blank=True, null=True)
    source_filename = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'confluence_pages'
        managed = False
        ordering = ['-page_updated_date']
    
    def __str__(self):
        return self.title
    
    def extract_ticket_references(self):
        """Extract Jira ticket references from page content"""
        pattern = r'PAY-\d+'
        matches = re.findall(pattern, self.content, re.IGNORECASE)
        return list(set([m.upper() for m in matches]))


class EntityReference(models.Model):
    """Links entities across different sources"""
    
    SOURCE_TYPE_CHOICES = [
        ('commit', 'Git Commit'),
        ('meeting', 'Meeting'),
        ('jira_ticket', 'Jira Ticket'),
        ('confluence', 'Confluence Page'),
    ]
    
    REFERENCE_TYPE_CHOICES = [
        ('jira_ticket', 'Jira Ticket'),
        ('commit', 'Git Commit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES)
    source_id = models.UUIDField()
    reference_type = models.CharField(max_length=50, choices=REFERENCE_TYPE_CHOICES)
    reference_id = models.CharField(max_length=100)
    extraction_method = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'entity_references'
        managed = False
        unique_together = ['source_type', 'source_id', 'reference_type', 'reference_id']
    
    def __str__(self):
        return f"{self.source_type}:{self.source_id} -> {self.reference_type}:{self.reference_id}"
    
class Project(models.Model):
    """Groups related tickets, commits, meetings, and pages"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    
    # Linking to Jira
    epic_key = models.CharField(max_length=50, blank=True, null=True)
    jira_project_key = models.CharField(max_length=20, blank=True, null=True)
    
    # Linking to other sources
    github_repo = models.CharField(max_length=255, blank=True, null=True)
    confluence_space_key = models.CharField(max_length=50, blank=True, null=True)
    
    # Dates
    start_date = models.DateField(blank=True, null=True)
    target_end_date = models.DateField(blank=True, null=True)
    actual_end_date = models.DateField(blank=True, null=True)
    
    # Metadata
    owner = models.CharField(max_length=255, blank=True, null=True)
    team_members = models.TextField(blank=True, null=True)  # JSON array
    tags = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        managed = False
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ProjectEntity(models.Model):
    """Links projects to specific entities"""
    
    ENTITY_TYPE_CHOICES = [
        ('commit', 'Git Commit'),
        ('meeting', 'Meeting'),
        ('jira_ticket', 'Jira Ticket'),
        ('confluence', 'Confluence Page'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='entities',
        db_column='project_id'
    )
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.UUIDField()
    added_manually = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_entities'
        managed = False
        unique_together = ['project', 'entity_type', 'entity_id']
    
    def __str__(self):
        return f"{self.project.name} - {self.entity_type}"