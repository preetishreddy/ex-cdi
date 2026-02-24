"""
Django Management Command: ingest_data

Usage:
    python manage.py ingest_data --commits /path/to/commits.json
    python manage.py ingest_data --meetings /path/to/meeting.vtt
    python manage.py ingest_data --jira /path/to/tickets.csv
    python manage.py ingest_data --confluence /path/to/page.md
"""

import json
import re
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from knowledge_base.models import (
    GitCommit, 
    GitCommitFile, 
    Meeting, 
    JiraTicket, 
    ConfluencePage,
    EntityReference
)


def extract_jira_references(text):
    """Extract Jira ticket references from any text"""
    if not text:
        return []
    pattern = r'PAY-\d+'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return list(set([m.upper() for m in matches]))


def create_entity_references(source_type, source_id, ticket_references, extraction_method):
    """Create EntityReference records"""
    created = 0
    for ticket_key in ticket_references:
        _, was_created = EntityReference.objects.get_or_create(
            source_type=source_type,
            source_id=source_id,
            reference_type='jira_ticket',
            reference_id=ticket_key,
            defaults={'extraction_method': extraction_method}
        )
        if was_created:
            created += 1
    return created


class Command(BaseCommand):
    help = 'Ingest data from git commits, meetings, Jira tickets, and Confluence pages'

    def add_arguments(self, parser):
        parser.add_argument('--commits', type=str, help='Path to commits JSON file')
        parser.add_argument('--meetings', type=str, help='Path to VTT file')
        parser.add_argument('--jira', type=str, help='Path to Jira CSV file')
        parser.add_argument('--confluence', type=str, help='Path to Confluence markdown file')

    def handle(self, *args, **options):
        if options['commits']:
            self.ingest_commits(options['commits'])
        
        if options['meetings']:
            self.ingest_meeting(options['meetings'])
        
        if options['jira']:
            self.ingest_jira(options['jira'])
        
        if options['confluence']:
            self.ingest_confluence(options['confluence'])

    def ingest_commits(self, filepath):
        """Ingest git commits from JSON file"""
        self.stdout.write(f'Ingesting commits from {filepath}...')
        
        with open(filepath, 'r') as f:
            commits_data = json.load(f)
        
        commits_created = 0
        files_created = 0
        refs_created = 0
        
        with transaction.atomic():
            for commit_data in commits_data:
                author_info = commit_data['commit']['author']
                commit_date = datetime.fromisoformat(
                    author_info['date'].replace('Z', '+00:00')
                )
                
                # Extract ticket references
                message = commit_data['commit']['message']
                ticket_refs = extract_jira_references(message)
                related_tickets = ', '.join(ticket_refs) if ticket_refs else None
                
                commit, created = GitCommit.objects.update_or_create(
                    sha=commit_data['sha'],
                    defaults={
                        'author_name': author_info['name'],
                        'author_email': author_info['email'],
                        'commit_date': commit_date,
                        'message': message,
                        'related_tickets': related_tickets,
                    }
                )
                
                if created:
                    commits_created += 1
                
                # Delete existing files and recreate
                commit.files.all().delete()
                
                for file_data in commit_data.get('files', []):
                    GitCommitFile.objects.create(
                        commit=commit,
                        filename=file_data['filename'],
                        additions=file_data.get('additions', 0),
                        deletions=file_data.get('deletions', 0),
                        status=file_data['status']
                    )
                    files_created += 1
                
                # Create entity references
                refs_created += create_entity_references(
                    'commit', str(commit.id), ticket_refs, 'commit_message'
                )
        
        self.stdout.write(self.style.SUCCESS(
            f'  Commits: {commits_created}, Files: {files_created}, References: {refs_created}'
        ))

    def ingest_meeting(self, filepath):
        """Ingest meeting from VTT file"""
        self.stdout.write(f'Ingesting meeting from {filepath}...')
        
        with open(filepath, 'r') as f:
            vtt_content = f.read()
        
        # Extract participants
        speaker_pattern = r'^([A-Za-z\s\']+):'
        speakers = set()
        for line in vtt_content.split('\n'):
            match = re.match(speaker_pattern, line.strip())
            if match:
                speaker = match.group(1).strip()
                if not re.match(r'^\d', speaker):
                    speakers.add(speaker)
        
        # Extract duration from last timestamp
        timestamp_pattern = r'(\d{2}:\d{2}:\d{2})'
        timestamps = re.findall(timestamp_pattern, vtt_content)
        duration_seconds = None
        if timestamps:
            last_ts = timestamps[-1]
            parts = last_ts.split(':')
            duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        
        # Get title from filename
        title = filepath.split('/')[-1].replace('.vtt', '').replace('_', ' ').title()
        
        with transaction.atomic():
            meeting = Meeting.objects.create(
                title=title,
                raw_vtt_content=vtt_content,
                participants=json.dumps(list(speakers)),
                duration_seconds=duration_seconds,
                source_filename=filepath.split('/')[-1],
            )
            
            # Create entity references
            ticket_refs = extract_jira_references(vtt_content)
            refs_created = create_entity_references(
                'meeting', str(meeting.id), ticket_refs, 'vtt_transcript'
            )
        
        self.stdout.write(self.style.SUCCESS(
            f'  Meeting created with {len(speakers)} participants, {refs_created} references'
        ))

    def ingest_jira(self, filepath):
        """Ingest Jira tickets from CSV file"""
        self.stdout.write(f'Ingesting Jira tickets from {filepath}...')
        
        tickets_created = 0
        refs_created = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            delimiter = '\t' if '\t' in sample else ','
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            with transaction.atomic():
                for row in reader:
                    # Parse dates
                    created_date = None
                    updated_date = None
                    resolved_date = None
                    
                    for date_str, attr in [
                        (row.get('Created', ''), 'created_date'),
                        (row.get('Updated', ''), 'updated_date'),
                        (row.get('Resolved', ''), 'resolved_date'),
                    ]:
                        if date_str:
                            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']:
                                try:
                                    parsed = datetime.strptime(date_str.strip(), fmt)
                                    if attr == 'created_date':
                                        created_date = timezone.make_aware(parsed)
                                    elif attr == 'updated_date':
                                        updated_date = timezone.make_aware(parsed)
                                    elif attr == 'resolved_date':
                                        resolved_date = timezone.make_aware(parsed)
                                    break
                                except ValueError:
                                    continue
                    
                    # Parse story points
                    sp = row.get('Story Points', '').strip()
                    story_points = int(sp) if sp.isdigit() else None
                    
                    ticket, created = JiraTicket.objects.update_or_create(
                        issue_key=row.get('Issue Key', '').strip(),
                        defaults={
                            'issue_type': row.get('Issue Type', '').strip(),
                            'summary': row.get('Summary', '').strip(),
                            'description': row.get('Description', '').strip() or None,
                            'status': row.get('Status', '').strip(),
                            'priority': row.get('Priority', '').strip() or None,
                            'assignee': row.get('Assignee', '').strip() or None,
                            'reporter': row.get('Reporter', '').strip() or None,
                            'created_date': created_date,
                            'updated_date': updated_date,
                            'resolved_date': resolved_date,
                            'labels': row.get('Labels', '').strip() or None,
                            'epic_link': row.get('Epic Link', '').strip() or None,
                            'sprint': row.get('Sprint', '').strip() or None,
                            'story_points': story_points,
                            'comments': row.get('Comments', '').strip() or None,
                        }
                    )
                    
                    if created:
                        tickets_created += 1
                    
                    # Create reference for epic link
                    if ticket.epic_link:
                        _, was_created = EntityReference.objects.get_or_create(
                            source_type='jira_ticket',
                            source_id=str(ticket.id),
                            reference_type='jira_ticket',
                            reference_id=ticket.epic_link,
                            defaults={'extraction_method': 'epic_link'}
                        )
                        if was_created:
                            refs_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'  Tickets: {tickets_created}, References: {refs_created}'
        ))

    def ingest_confluence(self, filepath):
        """Ingest Confluence page from Markdown file"""
        self.stdout.write(f'Ingesting Confluence page from {filepath}...')
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Parse frontmatter
        frontmatter = {}
        body = content
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                body = parts[2].strip()
                
                for line in yaml_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # Handle arrays
                        if value.startswith('[') and value.endswith(']'):
                            try:
                                value = json.loads(value)
                            except:
                                value = [v.strip().strip('"').strip("'") 
                                       for v in value[1:-1].split(',')]
                        
                        frontmatter[key] = value
        
        # Parse dates
        created_date = None
        updated_date = None
        if frontmatter.get('created'):
            try:
                created_date = timezone.make_aware(
                    datetime.strptime(frontmatter['created'], '%Y-%m-%d')
                )
            except ValueError:
                pass
        if frontmatter.get('last_updated'):
            try:
                updated_date = timezone.make_aware(
                    datetime.strptime(frontmatter['last_updated'], '%Y-%m-%d')
                )
            except ValueError:
                pass
        
        # Get labels
        labels = frontmatter.get('labels', [])
        if isinstance(labels, str):
            labels = [l.strip() for l in labels.split(',')]
        
        with transaction.atomic():
            page, created = ConfluencePage.objects.update_or_create(
                title=frontmatter.get('title', filepath.split('/')[-1]),
                space=frontmatter.get('space'),
                defaults={
                    'author': frontmatter.get('author'),
                    'content': body,
                    'labels': labels,
                    'version': int(frontmatter.get('version', 1)),
                    'page_created_date': created_date,
                    'page_updated_date': updated_date,
                    'source_filename': filepath.split('/')[-1],
                }
            )
            
            # Create entity references
            ticket_refs = extract_jira_references(body)
            refs_created = create_entity_references(
                'confluence', str(page.id), ticket_refs, 'content_body'
            )
        
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'  Page {status}, Labels: {labels}, References: {refs_created}'
        ))