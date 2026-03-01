"""
Django Management Command: ingest_data

Usage:
    python manage.py ingest_data --commits /path/to/commits.json
    python manage.py ingest_data --meetings /path/to/meeting.vtt
    python manage.py ingest_data --jira /path/to/tickets.csv
    python manage.py ingest_data --confluence /path/to/page.md
    python manage.py ingest_data --employees /path/to/employees.csv
    python manage.py ingest_data --projects /path/to/projects.csv
    python manage.py ingest_data --sprints /path/to/sprints.csv
    python manage.py ingest_data --sprint-tickets /path/to/sprint_tickets.csv
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
    EntityReference,
    Employee,
    Project,
    Sprint,
    SprintTicket
)


def extract_jira_references(text):
    """Extract Jira ticket references from any text"""
    if not text:
        return []
    # Updated pattern to match ONBOARD-XX, PAY-XX, etc.
    pattern = r'[A-Z]+-\d+'
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
    help = 'Ingest data from git commits, meetings, Jira tickets, Confluence pages, employees, projects, and sprints'

    def add_arguments(self, parser):
        parser.add_argument('--commits', type=str, help='Path to commits JSON file')
        parser.add_argument('--meetings', type=str, help='Path to VTT file')
        parser.add_argument('--jira', type=str, help='Path to Jira CSV file')
        parser.add_argument('--confluence', type=str, help='Path to Confluence markdown file')
        parser.add_argument('--employees', type=str, help='Path to employees CSV file')
        parser.add_argument('--projects', type=str, help='Path to projects CSV file')
        parser.add_argument('--sprints', type=str, help='Path to sprints CSV file')
        parser.add_argument('--sprint-tickets', type=str, help='Path to sprint_tickets CSV file')

    def handle(self, *args, **options):
        if options['commits']:
            self.ingest_commits(options['commits'])
        
        if options['meetings']:
            self.ingest_meeting(options['meetings'])
        
        if options['jira']:
            self.ingest_jira(options['jira'])
        
        if options['confluence']:
            self.ingest_confluence(options['confluence'])
        
        if options['employees']:
            self.ingest_employees(options['employees'])
        
        if options['projects']:
            self.ingest_projects(options['projects'])
        
        if options['sprints']:
            self.ingest_sprints(options['sprints'])
        
        if options['sprint_tickets']:
            self.ingest_sprint_tickets(options['sprint_tickets'])

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
        
        # Extract meeting date from NOTE section
        meeting_date = None
        date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', vtt_content)
        if date_match:
            try:
                meeting_date = timezone.make_aware(
                    datetime.strptime(date_match.group(1), '%Y-%m-%d')
                )
            except ValueError:
                pass
        
        # Extract title from NOTE section
        title_match = re.search(r'Meeting:\s*(.+)', vtt_content)
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = filepath.split('/')[-1].replace('.vtt', '').replace('_', ' ').title()
        
        # Extract participants from NOTE section
        participants_match = re.search(r'Participants:\s*(.+)', vtt_content)
        if participants_match:
            participants_str = participants_match.group(1).strip()
            speakers = set()
            for part in participants_str.split(','):
                name = re.sub(r'\s*\([^)]*\)', '', part).strip()
                if name:
                    speakers.add(name)
        else:
            # Fallback: extract from dialogue
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
        
        with transaction.atomic():
            meeting = Meeting.objects.create(
                title=title,
                meeting_date=meeting_date,
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
            f'  Meeting "{title}" created with {len(speakers)} participants, {refs_created} references'
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
        
        # Parse frontmatter (supports key: value at top without ---)
        frontmatter = {}
        body = content
        
        # Check for YAML frontmatter with ---
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
                        
                        if value.startswith('[') and value.endswith(']'):
                            try:
                                value = json.loads(value)
                            except:
                                value = [v.strip().strip('"').strip("'") 
                                       for v in value[1:-1].split(',')]
                        
                        frontmatter[key] = value
        else:
            # Check for key: value format at top (without ---)
            lines = content.split('\n')
            body_start = 0
            for i, line in enumerate(lines):
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip().strip('"').strip("'")
                    
                    if value.startswith('[') and value.endswith(']'):
                        try:
                            value = json.loads(value)
                        except:
                            value = [v.strip().strip('"').strip("'") 
                                   for v in value[1:-1].split(',')]
                    
                    frontmatter[key] = value
                    body_start = i + 1
                else:
                    if line.strip() and line.startswith('#'):
                        break
            
            body = '\n'.join(lines[body_start:]).strip()
        
        # Parse dates
        created_date = None
        updated_date = None
        for key in ['created', 'page_created_date']:
            if frontmatter.get(key):
                try:
                    created_date = timezone.make_aware(
                        datetime.strptime(frontmatter[key], '%Y-%m-%d')
                    )
                    break
                except ValueError:
                    pass
        
        for key in ['last_updated', 'page_updated_date', 'updated']:
            if frontmatter.get(key):
                try:
                    updated_date = timezone.make_aware(
                        datetime.strptime(frontmatter[key], '%Y-%m-%d')
                    )
                    break
                except ValueError:
                    pass
        
        # Get labels
        labels = frontmatter.get('labels', [])
        if isinstance(labels, str):
            labels = [l.strip() for l in labels.split(',')]
        
        # Get version
        version = 1
        if frontmatter.get('version'):
            try:
                version = int(frontmatter['version'])
            except (ValueError, TypeError):
                pass
        
        with transaction.atomic():
            page, created = ConfluencePage.objects.update_or_create(
                title=frontmatter.get('title', filepath.split('/')[-1].replace('.md', '')),
                space=frontmatter.get('space'),
                defaults={
                    'author': frontmatter.get('author'),
                    'content': body,
                    'labels': labels,
                    'version': version,
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
            f'  Page "{frontmatter.get("title", "Unknown")}" {status}, Labels: {labels}, References: {refs_created}'
        ))

    # ==========================================
    # NEW METHODS FOR EMPLOYEES, PROJECTS, SPRINTS
    # ==========================================

    def ingest_employees(self, filepath):
        """Ingest employees from CSV file"""
        self.stdout.write(f'Ingesting employees from {filepath}...')
        
        employees_created = 0
        employees_updated = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            with transaction.atomic():
                for row in reader:
                    # Parse is_active
                    is_active_str = row.get('is_active', 'true').strip().lower()
                    is_active = is_active_str in ['true', '1', 'yes', 't']
                    
                    employee, created = Employee.objects.update_or_create(
                        name=row.get('name', '').strip(),
                        defaults={
                            'email': row.get('email', '').strip() or None,
                            'role': row.get('role', '').strip() or None,
                            'department': row.get('department', '').strip() or None,
                            'source': row.get('source', '').strip() or 'csv',
                            'github_username': row.get('github_username', '').strip() or None,
                            'jira_account_id': row.get('jira_account_id', '').strip() or None,
                            'is_active': is_active,
                        }
                    )
                    
                    if created:
                        employees_created += 1
                    else:
                        employees_updated += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'  Employees created: {employees_created}, updated: {employees_updated}'
        ))

    def ingest_projects(self, filepath):
        """Ingest projects from CSV file"""
        self.stdout.write(f'Ingesting projects from {filepath}...')
        
        projects_created = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            with transaction.atomic():
                for row in reader:
                    # Parse dates
                    start_date = None
                    target_end_date = None
                    actual_end_date = None
                    
                    for date_str, attr in [
                        (row.get('start_date', ''), 'start_date'),
                        (row.get('target_end_date', ''), 'target_end_date'),
                        (row.get('actual_end_date', ''), 'actual_end_date'),
                    ]:
                        if date_str and date_str.strip():
                            try:
                                parsed = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
                                if attr == 'start_date':
                                    start_date = parsed
                                elif attr == 'target_end_date':
                                    target_end_date = parsed
                                elif attr == 'actual_end_date':
                                    actual_end_date = parsed
                            except ValueError:
                                pass
                    
                    # Parse tags
                    tags = []
                    tags_str = row.get('tags', '').strip()
                    if tags_str:
                        if tags_str.startswith('['):
                            try:
                                tags = json.loads(tags_str)
                            except:
                                tags = [t.strip().strip('"').strip("'") 
                                       for t in tags_str[1:-1].split(',')]
                        else:
                            tags = [t.strip() for t in tags_str.split(',')]
                    
                    project, created = Project.objects.update_or_create(
                        name=row.get('name', '').strip(),
                        defaults={
                            'description': row.get('description', '').strip() or None,
                            'status': row.get('status', 'active').strip(),
                            'epic_key': row.get('epic_key', '').strip() or None,
                            'jira_project_key': row.get('jira_project_key', '').strip() or None,
                            'github_repo': row.get('github_repo', '').strip() or None,
                            'confluence_space_key': row.get('confluence_space_key', '').strip() or None,
                            'start_date': start_date,
                            'target_end_date': target_end_date,
                            'actual_end_date': actual_end_date,
                            'owner': row.get('owner', '').strip() or None,
                            'team_members': row.get('team_members', '').strip() or None,
                            'tags': tags,
                        }
                    )
                    
                    if created:
                        projects_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'  Projects created: {projects_created}'
        ))

    def ingest_sprints(self, filepath):
        """Ingest sprints from CSV file"""
        self.stdout.write(f'Ingesting sprints from {filepath}...')
        
        sprints_created = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            with transaction.atomic():
                for row in reader:
                    # Parse dates
                    start_date = None
                    end_date = None
                    
                    if row.get('start_date', '').strip():
                        try:
                            start_date = datetime.strptime(row['start_date'].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    if row.get('end_date', '').strip():
                        try:
                            end_date = datetime.strptime(row['end_date'].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    # Find project by name
                    project = None
                    project_name = row.get('project_name', '').strip()
                    if project_name:
                        try:
                            project = Project.objects.get(name=project_name)
                        except Project.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f'  Warning: Project "{project_name}" not found for sprint'
                            ))
                    
                    sprint, created = Sprint.objects.update_or_create(
                        sprint_number=int(row.get('sprint_number', 0)),
                        project=project,
                        defaults={
                            'name': row.get('name', '').strip(),
                            'start_date': start_date,
                            'end_date': end_date,
                            'goal': row.get('goal', '').strip() or None,
                            'status': row.get('status', 'planned').strip(),
                        }
                    )
                    
                    if created:
                        sprints_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'  Sprints created: {sprints_created}'
        ))

    def ingest_sprint_tickets(self, filepath):
        """Ingest sprint-ticket relationships from CSV file"""
        self.stdout.write(f'Ingesting sprint-ticket links from {filepath}...')
        
        links_created = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            with transaction.atomic():
                for row in reader:
                    sprint_number = int(row.get('sprint_number', 0))
                    ticket_key = row.get('ticket_key', '').strip()
                    
                    # Parse added_date
                    added_date = None
                    if row.get('added_date', '').strip():
                        try:
                            added_date = datetime.strptime(row['added_date'].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    # Find sprint
                    try:
                        sprint = Sprint.objects.get(sprint_number=sprint_number)
                    except Sprint.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'  Warning: Sprint {sprint_number} not found'
                        ))
                        continue
                    
                    # Find ticket
                    try:
                        ticket = JiraTicket.objects.get(issue_key=ticket_key)
                    except JiraTicket.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'  Warning: Ticket {ticket_key} not found'
                        ))
                        continue
                    
                    _, created = SprintTicket.objects.get_or_create(
                        sprint=sprint,
                        ticket=ticket,
                        defaults={
                            'added_date': added_date,
                        }
                    )
                    
                    if created:
                        links_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'  Sprint-ticket links created: {links_created}'
        ))