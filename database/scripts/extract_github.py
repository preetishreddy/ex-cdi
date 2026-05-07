"""
GitHub Data Extraction Script

Extracts commits from a GitHub repository and stores them in the database.

Usage:
    python scripts/extract_github.py

Environment Variables Required:
    GITHUB_TOKEN - GitHub Personal Access Token
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
from knowledge_base.models import GitCommit, GitCommitFile, EntityReference
import re

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_BASE = 'https://api.github.com'


def get_headers():
    """Get headers for GitHub API requests"""
    return {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }


def extract_jira_references(text):
    """Extract Jira ticket references from text"""
    if not text:
        return []
    # Adjust pattern based on your Jira project keys
    pattern = r'[A-Z]+-\d+'
    matches = re.findall(pattern, text)
    return list(set(matches))


def get_commits(owner, repo, per_page=100, max_pages=10):
    """
    Fetch commits from a GitHub repository
    
    Args:
        owner: Repository owner (username or org)
        repo: Repository name
        per_page: Number of commits per page (max 100)
        max_pages: Maximum number of pages to fetch
    
    Returns:
        List of commit data
    """
    all_commits = []
    page = 1
    
    while page <= max_pages:
        url = f'{GITHUB_API_BASE}/repos/{owner}/{repo}/commits'
        params = {'per_page': per_page, 'page': page}
        
        print(f'Fetching commits page {page}...')
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code != 200:
            print(f'Error fetching commits: {response.status_code}')
            print(response.json())
            break
        
        commits = response.json()
        if not commits:
            break
        
        all_commits.extend(commits)
        print(f'  Found {len(commits)} commits')
        
        if len(commits) < per_page:
            break
        
        page += 1
    
    return all_commits


def get_commit_details(owner, repo, sha):
    """
    Get detailed commit information including files changed
    
    Args:
        owner: Repository owner
        repo: Repository name
        sha: Commit SHA
    
    Returns:
        Commit details with files
    """
    url = f'{GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{sha}'
    response = requests.get(url, headers=get_headers())
    
    if response.status_code != 200:
        print(f'Error fetching commit {sha}: {response.status_code}')
        return None
    
    return response.json()


def save_commit_to_db(commit_data, owner, repo):
    """
    Save a commit and its files to the database
    
    Args:
        commit_data: Commit data from GitHub API (with files)
        owner: Repository owner
        repo: Repository name
    
    Returns:
        Created or updated GitCommit object
    """
    commit_info = commit_data['commit']
    author_info = commit_info['author']
    
    # Parse commit date
    commit_date = datetime.fromisoformat(
        author_info['date'].replace('Z', '+00:00')
    )
    
    # Extract ticket references
    message = commit_info['message']
    ticket_refs = extract_jira_references(message)
    related_tickets = ', '.join(ticket_refs) if ticket_refs else None
    
    # Create or update commit
    commit, created = GitCommit.objects.update_or_create(
        sha=commit_data['sha'],
        defaults={
            'author_name': author_info.get('name', 'Unknown'),
            'author_email': author_info.get('email', 'unknown@unknown.com'),
            'commit_date': commit_date,
            'message': message,
            'related_tickets': related_tickets,
        }
    )
    
    # Delete existing files and recreate
    if not created:
        commit.files.all().delete()
    
    # Add files
    for file_data in commit_data.get('files', []):
        GitCommitFile.objects.create(
            commit=commit,
            filename=file_data['filename'],
            additions=file_data.get('additions', 0),
            deletions=file_data.get('deletions', 0),
            status=file_data.get('status', 'modified')
        )
    
    # Create entity references for ticket links
    for ticket_key in ticket_refs:
        EntityReference.objects.get_or_create(
            source_type='commit',
            source_id=commit.id,
            reference_type='jira_ticket',
            reference_id=ticket_key,
            defaults={'extraction_method': 'commit_message'}
        )
    
    return commit, created


def extract_repo(owner, repo, max_commits=100):
    """
    Extract all commits from a repository and save to database
    
    Args:
        owner: Repository owner (username or org)
        repo: Repository name
        max_commits: Maximum number of commits to extract
    """
    print(f'\n{"="*60}')
    print(f'Extracting commits from {owner}/{repo}')
    print(f'{"="*60}\n')
    
    # Fetch commit list
    commits = get_commits(owner, repo, per_page=100, max_pages=(max_commits // 100) + 1)
    commits = commits[:max_commits]
    
    print(f'\nTotal commits to process: {len(commits)}')
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    with transaction.atomic():
        for i, commit_summary in enumerate(commits, 1):
            sha = commit_summary['sha']
            print(f'\n[{i}/{len(commits)}] Processing {sha[:7]}...')
            
            # Get full commit details with files
            commit_details = get_commit_details(owner, repo, sha)
            
            if not commit_details:
                error_count += 1
                continue
            
            # Save to database
            commit, created = save_commit_to_db(commit_details, owner, repo)
            
            if created:
                created_count += 1
                print(f'  ✓ Created: {commit.message[:50]}...')
            else:
                updated_count += 1
                print(f'  ↻ Updated: {commit.message[:50]}...')
    
    print(f'\n{"="*60}')
    print(f'Extraction Complete!')
    print(f'{"="*60}')
    print(f'  Created: {created_count}')
    print(f'  Updated: {updated_count}')
    print(f'  Errors:  {error_count}')
    print(f'  Total:   {len(commits)}')


def main():
    """Main entry point"""
    if not GITHUB_TOKEN:
        print('Error: GITHUB_TOKEN environment variable not set')
        print('Add GITHUB_TOKEN=your_token to your .env file')
        sys.exit(1)
    
    # Default repository - change these or make them command line args
    owner = os.getenv('GITHUB_OWNER', 'nkousik18')
    repo = os.getenv('GITHUB_REPO', 'LoanQA-MLOps')
    max_commits = int(os.getenv('GITHUB_MAX_COMMITS', '100'))
    
    print(f'GitHub Token: {GITHUB_TOKEN[:10]}...')
    print(f'Repository: {owner}/{repo}')
    print(f'Max Commits: {max_commits}')
    
    extract_repo(owner, repo, max_commits)


if __name__ == '__main__':
    main()