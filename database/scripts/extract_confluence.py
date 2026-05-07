"""
Confluence Data Extraction Script

Extracts pages from a Confluence space and stores them in the database.

Usage:
    python scripts/extract_confluence.py

Environment Variables Required:
    CONFLUENCE_DOMAIN - Your Atlassian domain (e.g., onboardingaii.atlassian.net)
    CONFLUENCE_EMAIL - Your Atlassian email
    CONFLUENCE_API_TOKEN - Your Atlassian API token
    CONFLUENCE_SPACE_ID - Space ID to extract from
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import html
import re

# Add parent directory to path for Django imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.db import transaction
from django.utils import timezone
from knowledge_base.models import ConfluencePage, EntityReference

# Load environment variables
load_dotenv()

CONFLUENCE_DOMAIN = os.getenv('CONFLUENCE_DOMAIN')
CONFLUENCE_EMAIL = os.getenv('CONFLUENCE_EMAIL')
CONFLUENCE_API_TOKEN = os.getenv('CONFLUENCE_API_TOKEN')
CONFLUENCE_SPACE_ID = os.getenv('CONFLUENCE_SPACE_ID')
CONFLUENCE_SPACE_KEY = os.getenv('CONFLUENCE_SPACE_KEY', 'ONBOARD')

# Cache for user display names
USER_CACHE = {}


def get_auth():
    """Get authentication tuple for requests"""
    return (CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)


def get_headers():
    """Get headers for Confluence API requests"""
    return {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }


def get_user_display_name(account_id):
    """
    Get user display name from Atlassian account ID
    
    Args:
        account_id: Atlassian account ID (e.g., "712020:f6f2386a-1730-44fd-a9a3-0fda6ca10d69")
    
    Returns:
        Display name (e.g., "Ash Ketchum") or account_id if not found
    """
    if not account_id:
        return None
    
    # Check cache first
    if account_id in USER_CACHE:
        return USER_CACHE[account_id]
    
    # Fetch from API
    url = f'https://{CONFLUENCE_DOMAIN}/wiki/rest/api/user?accountId={account_id}'
    
    try:
        response = requests.get(url, auth=get_auth(), headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            display_name = data.get('displayName', account_id)
            USER_CACHE[account_id] = display_name
            return display_name
    except Exception as e:
        print(f'  Warning: Could not fetch user name for {account_id}: {e}')
    
    # Fallback to account_id
    USER_CACHE[account_id] = account_id
    return account_id


def extract_jira_references(text):
    """Extract Jira ticket references from text"""
    if not text:
        return []
    # Adjust pattern based on your Jira project keys
    pattern = r'[A-Z]+-\d+'
    matches = re.findall(pattern, text)
    return list(set(matches))


def html_to_markdown(html_content):
    """
    Convert Confluence HTML/XML content to readable Markdown
    """
    if not html_content:
        return ''
    
    text = html_content
    
    # Handle Confluence-specific macros (code blocks)
    # Extract code from CDATA sections
    def replace_code_block(match):
        code = match.group(1) if match.group(1) else ''
        return f'\n```\n{code}\n```\n'
    
    text = re.sub(
        r'<ac:structured-macro[^>]*ac:name="code"[^>]*>.*?<ac:plain-text-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-body></ac:structured-macro>',
        replace_code_block,
        text,
        flags=re.DOTALL
    )
    
    # Remove remaining Confluence macros
    text = re.sub(r'<ac:structured-macro[^>]*>.*?</ac:structured-macro>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ac:[^>]+/?>', '', text)
    
    # Convert headers
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', text, flags=re.DOTALL)
    
    # Convert text formatting
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text, flags=re.DOTALL)
    
    # Convert lists
    text = re.sub(r'<ul[^>]*>', '\n', text)
    text = re.sub(r'</ul>', '\n', text)
    text = re.sub(r'<ol[^>]*>', '\n', text)
    text = re.sub(r'</ol>', '\n', text)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', text, flags=re.DOTALL)
    
    # Convert tables to simple text representation
    text = re.sub(r'<table[^>]*>', '\n', text)
    text = re.sub(r'</table>', '\n', text)
    text = re.sub(r'<tbody>', '', text)
    text = re.sub(r'</tbody>', '', text)
    text = re.sub(r'<tr[^>]*>', '', text)
    text = re.sub(r'</tr>', '\n', text)
    text = re.sub(r'<th[^>]*>(.*?)</th>', r'| **\1** ', text, flags=re.DOTALL)
    text = re.sub(r'<td[^>]*>(.*?)</td>', r'| \1 ', text, flags=re.DOTALL)
    
    # Convert line breaks and paragraphs
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<hr[^>]*/>', '\n---\n', text)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL)
    
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
    text = re.sub(r' +', ' ', text)  # Single spaces
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)  # Leading whitespace per line
    text = text.strip()
    
    return text


def html_to_text(html_content):
    """
    Convert HTML content to plain text (for searching)
    """
    if not html_content:
        return ''
    
    # First convert to markdown
    markdown = html_to_markdown(html_content)
    
    # Then strip markdown formatting for plain text search
    text = re.sub(r'[#*`|_\-]', '', markdown)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def get_spaces():
    """Fetch all spaces from Confluence"""
    url = f'https://{CONFLUENCE_DOMAIN}/wiki/api/v2/spaces'
    
    response = requests.get(url, auth=get_auth(), headers=get_headers())
    
    if response.status_code != 200:
        print(f'Error fetching spaces: {response.status_code}')
        print(response.text)
        return []
    
    return response.json().get('results', [])


def get_pages(space_id):
    """
    Fetch all pages from a Confluence space
    
    Args:
        space_id: Confluence space ID
    
    Returns:
        List of page data
    """
    all_pages = []
    url = f'https://{CONFLUENCE_DOMAIN}/wiki/api/v2/spaces/{space_id}/pages'
    
    while url:
        print(f'Fetching pages...')
        response = requests.get(url, auth=get_auth(), headers=get_headers())
        
        if response.status_code != 200:
            print(f'Error fetching pages: {response.status_code}')
            print(response.text)
            break
        
        data = response.json()
        pages = data.get('results', [])
        all_pages.extend(pages)
        print(f'  Found {len(pages)} pages')
        
        # Check for next page
        url = data.get('_links', {}).get('next')
        if url:
            url = f'https://{CONFLUENCE_DOMAIN}/wiki{url}'
    
    return all_pages


def get_page_content(page_id):
    """
    Get full page content
    
    Args:
        page_id: Confluence page ID
    
    Returns:
        Page data with body content
    """
    url = f'https://{CONFLUENCE_DOMAIN}/wiki/api/v2/pages/{page_id}?body-format=storage'
    
    response = requests.get(url, auth=get_auth(), headers=get_headers())
    
    if response.status_code != 200:
        print(f'Error fetching page {page_id}: {response.status_code}')
        return None
    
    return response.json()


def get_page_labels(page_id):
    """
    Get labels for a page
    
    Args:
        page_id: Confluence page ID
    
    Returns:
        List of label names
    """
    url = f'https://{CONFLUENCE_DOMAIN}/wiki/api/v2/pages/{page_id}/labels'
    
    response = requests.get(url, auth=get_auth(), headers=get_headers())
    
    if response.status_code != 200:
        print(f'Error fetching labels for page {page_id}: {response.status_code}')
        return []
    
    labels = response.json().get('results', [])
    return [label.get('name', '') for label in labels if label.get('name')]


def save_page_to_db(page_data, space_key, labels=None):
    """
    Save a Confluence page to the database
    
    Args:
        page_data: Page data from Confluence API
        space_key: Space key
        labels: List of label names
    
    Returns:
        Created or updated ConfluencePage object
    """
    # Extract content
    body = page_data.get('body', {})
    storage = body.get('storage', {})
    html_content = storage.get('value', '')
    
    # Convert to readable Markdown
    markdown_content = html_to_markdown(html_content)
    
    # Also get plain text for searching/entity extraction
    text_content = html_to_text(html_content)
    
    # Parse dates
    created_at = page_data.get('createdAt')
    if created_at:
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    
    version_info = page_data.get('version', {})
    updated_at = version_info.get('createdAt')
    if updated_at:
        updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
    
    # Get author display name (not just ID)
    author_id = page_data.get('authorId', '')
    author_name = get_user_display_name(author_id) if author_id else None
    
    # Create or update page - store MARKDOWN content (readable)
    page, created = ConfluencePage.objects.update_or_create(
        title=page_data.get('title', 'Untitled'),
        space=space_key,
        defaults={
            'author': author_name,  # Store display name instead of ID
            'content': markdown_content,  # Store readable Markdown
            'labels': labels or [],
            'version': version_info.get('number', 1),
            'page_created_date': created_at,
            'page_updated_date': updated_at,
            'source_filename': f"confluence_{page_data.get('id')}.md",
        }
    )
    
    # Extract and create entity references from plain text
    ticket_refs = extract_jira_references(text_content)
    for ticket_key in ticket_refs:
        EntityReference.objects.get_or_create(
            source_type='confluence',
            source_id=page.id,
            reference_type='jira_ticket',
            reference_id=ticket_key,
            defaults={'extraction_method': 'content_body'}
        )
    
    return page, created


def extract_space(space_id, space_key):
    """
    Extract all pages from a Confluence space and save to database
    
    Args:
        space_id: Confluence space ID
        space_key: Confluence space key
    """
    print(f'\n{"="*60}')
    print(f'Extracting pages from space: {space_key} (ID: {space_id})')
    print(f'{"="*60}\n')
    
    # Fetch page list
    pages = get_pages(space_id)
    
    print(f'\nTotal pages to process: {len(pages)}')
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    with transaction.atomic():
        for i, page_summary in enumerate(pages, 1):
            page_id = page_summary['id']
            title = page_summary.get('title', 'Untitled')
            
            print(f'\n[{i}/{len(pages)}] Processing: {title}')
            
            # Skip template pages
            if title.startswith('Template -'):
                print(f'  ⊘ Skipping template page')
                continue
            
            # Get full page content
            page_data = get_page_content(page_id)
            
            if not page_data:
                error_count += 1
                continue
            
            # Get labels
            labels = get_page_labels(page_id)
            
            # Save to database
            page, created = save_page_to_db(page_data, space_key, labels)
            
            if created:
                created_count += 1
                print(f'  ✓ Created: {page.title}')
            else:
                updated_count += 1
                print(f'  ↻ Updated: {page.title}')
            
            if labels:
                print(f'    Labels: {", ".join(labels)}')
    
    print(f'\n{"="*60}')
    print(f'Extraction Complete!')
    print(f'{"="*60}')
    print(f'  Created: {created_count}')
    print(f'  Updated: {updated_count}')
    print(f'  Errors:  {error_count}')
    print(f'  Total:   {len(pages)}')


def main():
    """Main entry point"""
    # Validate environment variables
    missing = []
    if not CONFLUENCE_DOMAIN:
        missing.append('CONFLUENCE_DOMAIN')
    if not CONFLUENCE_EMAIL:
        missing.append('CONFLUENCE_EMAIL')
    if not CONFLUENCE_API_TOKEN:
        missing.append('CONFLUENCE_API_TOKEN')
    if not CONFLUENCE_SPACE_ID:
        missing.append('CONFLUENCE_SPACE_ID')
    
    if missing:
        print(f'Error: Missing environment variables: {", ".join(missing)}')
        print('Add them to your .env file')
        sys.exit(1)
    
    print(f'Confluence Domain: {CONFLUENCE_DOMAIN}')
    print(f'Email: {CONFLUENCE_EMAIL}')
    print(f'Space ID: {CONFLUENCE_SPACE_ID}')
    print(f'Space Key: {CONFLUENCE_SPACE_KEY}')
    
    extract_space(CONFLUENCE_SPACE_ID, CONFLUENCE_SPACE_KEY)


if __name__ == '__main__':
    main()