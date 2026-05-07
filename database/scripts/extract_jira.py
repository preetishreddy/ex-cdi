"""
Jira Data Extraction Script

Extracts tickets from a Jira project and stores them in the database.

Usage:
    python scripts/extract_jira.py

Environment Variables Required:
    JIRA_DOMAIN - Your Atlassian domain (e.g., onboardingaii.atlassian.net)
    JIRA_EMAIL - Your Atlassian email
    JIRA_API_TOKEN - Your Atlassian API token
    JIRA_PROJECT_KEY - Project key to extract from (e.g., ONBOARD)
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for Django imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import transaction
from django.utils import timezone
from knowledge_base.models import JiraTicket, EntityReference

# Load environment variables
load_dotenv()

JIRA_DOMAIN = os.getenv('JIRA_DOMAIN')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'ONBOARD')


def get_auth():
    """Get authentication tuple for requests"""
    return (JIRA_EMAIL, JIRA_API_TOKEN)


def get_headers():
    """Get headers for Jira API requests"""
    return {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }


def parse_jira_date(date_str):
    """Parse Jira date string to datetime object"""
    if not date_str:
        return None
    try:
        # Jira dates are in ISO format
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        return None


def search_issues(jql, max_results=100):
    """
    Search Jira issues using JQL (using new /search/jql endpoint)
    
    Args:
        jql: JQL query string
        max_results: Maximum number of results to return
    
    Returns:
        List of issue data
    """
    all_issues = []
    next_page_token = None
    
    while True:
        url = f'https://{JIRA_DOMAIN}/rest/api/3/search/jql'
        
        # Build request body
        body = {
            'jql': jql,
            'maxResults': min(50, max_results - len(all_issues)),
            'fields': [
                'summary', 'description', 'status', 'priority', 
                'assignee', 'reporter', 'created', 'updated', 
                'resolutiondate', 'labels', 'issuetype',
                'parent', 'customfield_10020',  # Sprint field (may vary)
                'customfield_10016',  # Story points (may vary)
                'comment'
            ]
        }
        
        if next_page_token:
            body['nextPageToken'] = next_page_token
        
        print(f'Fetching issues...')
        response = requests.post(url, auth=get_auth(), headers=get_headers(), json=body)
        
        if response.status_code != 200:
            print(f'Error fetching issues: {response.status_code}')
            print(response.text)
            break
        
        data = response.json()
        issues = data.get('issues', [])
        all_issues.extend(issues)
        print(f'  Found {len(issues)} issues (total: {len(all_issues)})')
        
        # Check if we have more results
        next_page_token = data.get('nextPageToken')
        if not next_page_token or len(all_issues) >= max_results:
            break
    
    return all_issues[:max_results]


def get_issue_comments(issue_key):
    """
    Get comments for an issue
    
    Args:
        issue_key: Issue key (e.g., ONBOARD-1)
    
    Returns:
        List of comment data
    """
    url = f'https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/comment'
    
    response = requests.get(url, auth=get_auth(), headers=get_headers())
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    comments = []
    
    for comment in data.get('comments', []):
        # Extract comment text from Atlassian Document Format
        body = comment.get('body', {})
        text = extract_text_from_adf(body)
        
        comments.append({
            'author': comment.get('author', {}).get('displayName', 'Unknown'),
            'created': comment.get('created', ''),
            'text': text
        })
    
    return comments


def extract_text_from_adf(adf_content):
    """
    Extract plain text from Atlassian Document Format (ADF)
    
    Args:
        adf_content: ADF JSON content
    
    Returns:
        Plain text string
    """
    if not adf_content:
        return ''
    
    if isinstance(adf_content, str):
        return adf_content
    
    text_parts = []
    
    def extract_recursive(node):
        if isinstance(node, dict):
            if node.get('type') == 'text':
                text_parts.append(node.get('text', ''))
            for child in node.get('content', []):
                extract_recursive(child)
        elif isinstance(node, list):
            for item in node:
                extract_recursive(item)
    
    extract_recursive(adf_content)
    return ' '.join(text_parts)


def save_issue_to_db(issue_data):
    """
    Save a Jira issue to the database
    
    Args:
        issue_data: Issue data from Jira API
    
    Returns:
        Created or updated JiraTicket object
    """
    fields = issue_data.get('fields', {})
    
    # Extract basic fields
    issue_key = issue_data.get('key', '')
    issue_type = fields.get('issuetype', {}).get('name', 'Task')
    summary = fields.get('summary', '')
    
    # Description (ADF format)
    description = extract_text_from_adf(fields.get('description'))
    
    # Status and priority
    status = fields.get('status', {}).get('name', 'Unknown')
    priority = fields.get('priority', {}).get('name') if fields.get('priority') else None
    
    # People
    assignee = fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None
    reporter = fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None
    
    # Dates
    created_date = parse_jira_date(fields.get('created'))
    updated_date = parse_jira_date(fields.get('updated'))
    resolved_date = parse_jira_date(fields.get('resolutiondate'))
    
    # Labels
    labels = fields.get('labels', [])
    labels_str = ', '.join(labels) if labels else None
    
    # Epic link (parent)
    parent = fields.get('parent', {})
    epic_link = parent.get('key') if parent else None
    
    # Sprint (custom field - may vary by Jira instance)
    sprint_data = fields.get('customfield_10020')
    sprint = None
    if sprint_data and isinstance(sprint_data, list) and len(sprint_data) > 0:
        sprint = sprint_data[0].get('name') if isinstance(sprint_data[0], dict) else str(sprint_data[0])
    
    # Story points (custom field - may vary by Jira instance)
    story_points = fields.get('customfield_10016')
    if story_points:
        try:
            story_points = int(float(story_points))
        except (ValueError, TypeError):
            story_points = None
    
    # Get comments
    comments = get_issue_comments(issue_key)
    comments_json = json.dumps(comments) if comments else None
    
    # Create or update ticket
    ticket, created = JiraTicket.objects.update_or_create(
        issue_key=issue_key,
        defaults={
            'issue_type': issue_type,
            'summary': summary,
            'description': description,
            'status': status,
            'priority': priority,
            'assignee': assignee,
            'reporter': reporter,
            'created_date': created_date,
            'updated_date': updated_date,
            'resolved_date': resolved_date,
            'labels': labels_str,
            'epic_link': epic_link,
            'sprint': sprint,
            'story_points': story_points,
            'comments': comments_json,
        }
    )
    
    # Create entity reference for epic link
    if epic_link:
        EntityReference.objects.get_or_create(
            source_type='jira_ticket',
            source_id=ticket.id,
            reference_type='jira_ticket',
            reference_id=epic_link,
            defaults={'extraction_method': 'epic_link'}
        )
    
    return ticket, created


def extract_project(project_key, max_issues=500):
    """
    Extract all issues from a Jira project and save to database
    
    Args:
        project_key: Jira project key (e.g., ONBOARD)
        max_issues: Maximum number of issues to extract
    """
    print(f'\n{"="*60}')
    print(f'Extracting issues from project: {project_key}')
    print(f'{"="*60}\n')
    
    # Build JQL query
    jql = f'project = {project_key} ORDER BY created DESC'
    
    # Fetch issues
    issues = search_issues(jql, max_results=max_issues)
    
    print(f'\nTotal issues to process: {len(issues)}')
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    with transaction.atomic():
        for i, issue_data in enumerate(issues, 1):
            issue_key = issue_data.get('key', 'Unknown')
            summary = issue_data.get('fields', {}).get('summary', '')[:50]
            
            print(f'\n[{i}/{len(issues)}] Processing: {issue_key} - {summary}...')
            
            try:
                ticket, created = save_issue_to_db(issue_data)
                
                if created:
                    created_count += 1
                    print(f'  ✓ Created')
                else:
                    updated_count += 1
                    print(f'  ↻ Updated')
            except Exception as e:
                error_count += 1
                print(f'  ✗ Error: {str(e)}')
    
    print(f'\n{"="*60}')
    print(f'Extraction Complete!')
    print(f'{"="*60}')
    print(f'  Created: {created_count}')
    print(f'  Updated: {updated_count}')
    print(f'  Errors:  {error_count}')
    print(f'  Total:   {len(issues)}')


def main():
    """Main entry point"""
    # Validate environment variables
    missing = []
    if not JIRA_DOMAIN:
        missing.append('JIRA_DOMAIN')
    if not JIRA_EMAIL:
        missing.append('JIRA_EMAIL')
    if not JIRA_API_TOKEN:
        missing.append('JIRA_API_TOKEN')
    
    if missing:
        print(f'Error: Missing environment variables: {", ".join(missing)}')
        print('Add them to your .env file')
        sys.exit(1)
    
    print(f'Jira Domain: {JIRA_DOMAIN}')
    print(f'Email: {JIRA_EMAIL}')
    print(f'Project: {JIRA_PROJECT_KEY}')
    
    max_issues = int(os.getenv('JIRA_MAX_ISSUES', '500'))
    
    extract_project(JIRA_PROJECT_KEY, max_issues)


if __name__ == '__main__':
    main()