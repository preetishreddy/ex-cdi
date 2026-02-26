"""
Ingestion logic for all data sources.
Called by ingest API views to sync data from external sources into the database.
"""

import os
import json
import re
import html as html_module
import requests
from datetime import datetime
from django.db import transaction
from knowledge_base.models import (
    GitCommit, GitCommitFile, JiraTicket, ConfluencePage,
    Meeting, EntityReference,
)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _extract_jira_refs(text):
    if not text:
        return []
    matches = re.findall(r'PAY-\d+', text, re.IGNORECASE)
    return list(set([m.upper() for m in matches]))


def _create_entity_refs(source_type, source_id, ticket_refs, method):
    created = 0
    for key in ticket_refs:
        _, was_created = EntityReference.objects.get_or_create(
            source_type=source_type,
            source_id=source_id,
            reference_type='jira_ticket',
            reference_id=key,
            defaults={'extraction_method': method},
        )
        if was_created:
            created += 1
    return created


# ── GitHub ────────────────────────────────────────────────────────────────────

def run_github_ingest():
    token = os.getenv('GITHUB_TOKEN')
    owner = os.getenv('GITHUB_OWNER')
    repo = os.getenv('GITHUB_REPO')
    max_commits = int(os.getenv('GITHUB_MAX_COMMITS', '100'))

    if not token:
        raise ValueError('GITHUB_TOKEN not set in environment')
    if not owner or not repo:
        raise ValueError('GITHUB_OWNER and GITHUB_REPO must be set in environment')

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    # Fetch commit list
    all_commits = []
    page = 1
    max_pages = (max_commits // 100) + 1
    while page <= max_pages:
        resp = requests.get(
            f'https://api.github.com/repos/{owner}/{repo}/commits',
            headers=headers,
            params={'per_page': 100, 'page': page},
        )
        if resp.status_code != 200:
            raise Exception(f'GitHub API error {resp.status_code}: {resp.text}')
        commits = resp.json()
        if not commits:
            break
        all_commits.extend(commits)
        if len(commits) < 100:
            break
        page += 1

    all_commits = all_commits[:max_commits]
    created_count = updated_count = error_count = 0

    with transaction.atomic():
        for commit_summary in all_commits:
            sha = commit_summary['sha']
            try:
                detail_resp = requests.get(
                    f'https://api.github.com/repos/{owner}/{repo}/commits/{sha}',
                    headers=headers,
                )
                if detail_resp.status_code != 200:
                    error_count += 1
                    continue

                commit_data = detail_resp.json()
                commit_info = commit_data['commit']
                author_info = commit_info['author']
                commit_date = datetime.fromisoformat(
                    author_info['date'].replace('Z', '+00:00')
                )
                message = commit_info['message']
                ticket_refs = _extract_jira_refs(message)

                commit, created = GitCommit.objects.update_or_create(
                    sha=sha,
                    defaults={
                        'author_name': author_info.get('name', 'Unknown'),
                        'author_email': author_info.get('email', 'unknown@unknown.com'),
                        'commit_date': commit_date,
                        'message': message,
                        'related_tickets': ', '.join(ticket_refs) or None,
                    },
                )

                if not created:
                    commit.files.all().delete()

                for file_data in commit_data.get('files', []):
                    GitCommitFile.objects.create(
                        commit=commit,
                        filename=file_data['filename'],
                        additions=file_data.get('additions', 0),
                        deletions=file_data.get('deletions', 0),
                        status=file_data.get('status', 'modified'),
                    )

                _create_entity_refs('commit', str(commit.id), ticket_refs, 'commit_message')

                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception:
                error_count += 1

    return {
        'source': 'github',
        'repository': f'{owner}/{repo}',
        'created': created_count,
        'updated': updated_count,
        'errors': error_count,
        'total': len(all_commits),
    }


# ── Jira ──────────────────────────────────────────────────────────────────────

def _extract_text_from_adf(adf):
    if not adf:
        return ''
    if isinstance(adf, str):
        return adf
    parts = []

    def walk(node):
        if isinstance(node, dict):
            if node.get('type') == 'text':
                parts.append(node.get('text', ''))
            for child in node.get('content', []):
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(adf)
    return ' '.join(parts)


def run_jira_ingest():
    domain = os.getenv('JIRA_DOMAIN')
    email = os.getenv('JIRA_EMAIL')
    token = os.getenv('JIRA_API_TOKEN')
    project_key = os.getenv('JIRA_PROJECT_KEY', 'PAY')
    max_issues = int(os.getenv('JIRA_MAX_ISSUES', '500'))

    if not domain or not email or not token:
        raise ValueError('JIRA_DOMAIN, JIRA_EMAIL, and JIRA_API_TOKEN must be set in environment')

    auth = (email, token)
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    # Fetch all issues
    all_issues = []
    next_page_token = None
    while True:
        body = {
            'jql': f'project = {project_key} ORDER BY created DESC',
            'maxResults': min(50, max_issues - len(all_issues)),
            'fields': [
                'summary', 'description', 'status', 'priority',
                'assignee', 'reporter', 'created', 'updated',
                'resolutiondate', 'labels', 'issuetype',
                'parent', 'customfield_10020', 'customfield_10016',
            ],
        }
        if next_page_token:
            body['nextPageToken'] = next_page_token

        resp = requests.post(
            f'https://{domain}/rest/api/3/search/jql',
            auth=auth, headers=headers, json=body,
        )
        if resp.status_code != 200:
            raise Exception(f'Jira API error {resp.status_code}: {resp.text}')

        data = resp.json()
        issues = data.get('issues', [])
        all_issues.extend(issues)
        next_page_token = data.get('nextPageToken')
        if not next_page_token or len(all_issues) >= max_issues:
            break

    created_count = updated_count = error_count = 0

    def _parse_date(s):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        except ValueError:
            return None

    with transaction.atomic():
        for issue_data in all_issues:
            try:
                fields = issue_data.get('fields', {})
                issue_key = issue_data.get('key', '')

                parent = fields.get('parent') or {}
                epic_link = parent.get('key')

                sprint_data = fields.get('customfield_10020')
                sprint = None
                if sprint_data and isinstance(sprint_data, list) and sprint_data:
                    sprint = sprint_data[0].get('name') if isinstance(sprint_data[0], dict) else str(sprint_data[0])

                sp = fields.get('customfield_10016')
                story_points = None
                if sp:
                    try:
                        story_points = int(float(sp))
                    except (ValueError, TypeError):
                        pass

                ticket, created = JiraTicket.objects.update_or_create(
                    issue_key=issue_key,
                    defaults={
                        'issue_type': fields.get('issuetype', {}).get('name', 'Task'),
                        'summary': fields.get('summary', ''),
                        'description': _extract_text_from_adf(fields.get('description')),
                        'status': fields.get('status', {}).get('name', 'Unknown'),
                        'priority': (fields.get('priority') or {}).get('name'),
                        'assignee': (fields.get('assignee') or {}).get('displayName'),
                        'reporter': (fields.get('reporter') or {}).get('displayName'),
                        'created_date': _parse_date(fields.get('created')),
                        'updated_date': _parse_date(fields.get('updated')),
                        'resolved_date': _parse_date(fields.get('resolutiondate')),
                        'labels': ', '.join(fields.get('labels', [])) or None,
                        'epic_link': epic_link,
                        'sprint': sprint,
                        'story_points': story_points,
                    },
                )

                if epic_link:
                    EntityReference.objects.get_or_create(
                        source_type='jira_ticket',
                        source_id=ticket.id,
                        reference_type='jira_ticket',
                        reference_id=epic_link,
                        defaults={'extraction_method': 'epic_link'},
                    )

                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception:
                error_count += 1

    return {
        'source': 'jira',
        'project': project_key,
        'created': created_count,
        'updated': updated_count,
        'errors': error_count,
        'total': len(all_issues),
    }


# ── Confluence ────────────────────────────────────────────────────────────────

def _html_to_markdown(html_content):
    if not html_content:
        return ''
    text = html_content
    text = re.sub(
        r'<ac:structured-macro[^>]*ac:name="code"[^>]*>.*?'
        r'<ac:plain-text-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-body>'
        r'</ac:structured-macro>',
        lambda m: f'\n```\n{m.group(1)}\n```\n',
        text, flags=re.DOTALL,
    )
    text = re.sub(r'<ac:structured-macro[^>]*>.*?</ac:structured-macro>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ac:[^>]+/?>', '', text)
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_module.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def run_confluence_ingest():
    domain = os.getenv('CONFLUENCE_DOMAIN')
    email = os.getenv('CONFLUENCE_EMAIL')
    token = os.getenv('CONFLUENCE_API_TOKEN')
    space_id = os.getenv('CONFLUENCE_SPACE_ID')
    space_key = os.getenv('CONFLUENCE_SPACE_KEY', 'ONBOARD')

    if not domain or not email or not token or not space_id:
        raise ValueError(
            'CONFLUENCE_DOMAIN, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN, '
            'and CONFLUENCE_SPACE_ID must be set in environment'
        )

    auth = (email, token)
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    user_cache = {}

    def get_user_name(account_id):
        if not account_id:
            return None
        if account_id in user_cache:
            return user_cache[account_id]
        try:
            resp = requests.get(
                f'https://{domain}/wiki/rest/api/user?accountId={account_id}',
                auth=auth, headers=headers,
            )
            if resp.status_code == 200:
                name = resp.json().get('displayName', account_id)
                user_cache[account_id] = name
                return name
        except Exception:
            pass
        user_cache[account_id] = account_id
        return account_id

    # Fetch all pages
    all_pages = []
    url = f'https://{domain}/wiki/api/v2/spaces/{space_id}/pages'
    while url:
        resp = requests.get(url, auth=auth, headers=headers)
        if resp.status_code != 200:
            raise Exception(f'Confluence API error {resp.status_code}: {resp.text}')
        data = resp.json()
        all_pages.extend(data.get('results', []))
        next_url = data.get('_links', {}).get('next')
        url = f'https://{domain}/wiki{next_url}' if next_url else None

    created_count = updated_count = error_count = 0

    def _parse_dt(s):
        return datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None

    with transaction.atomic():
        for page_summary in all_pages:
            title = page_summary.get('title', 'Untitled')
            if title.startswith('Template -'):
                continue
            try:
                page_id = page_summary['id']

                content_resp = requests.get(
                    f'https://{domain}/wiki/api/v2/pages/{page_id}?body-format=storage',
                    auth=auth, headers=headers,
                )
                if content_resp.status_code != 200:
                    error_count += 1
                    continue
                page_data = content_resp.json()

                labels_resp = requests.get(
                    f'https://{domain}/wiki/api/v2/pages/{page_id}/labels',
                    auth=auth, headers=headers,
                )
                labels = []
                if labels_resp.status_code == 200:
                    labels = [
                        l.get('name', '') for l in labels_resp.json().get('results', [])
                        if l.get('name')
                    ]

                html_content = page_data.get('body', {}).get('storage', {}).get('value', '')
                markdown_content = _html_to_markdown(html_content)
                version_info = page_data.get('version', {})

                page, created = ConfluencePage.objects.update_or_create(
                    title=title,
                    space=space_key,
                    defaults={
                        'author': get_user_name(page_data.get('authorId')),
                        'content': markdown_content,
                        'labels': labels,
                        'version': version_info.get('number', 1),
                        'page_created_date': _parse_dt(page_data.get('createdAt')),
                        'page_updated_date': _parse_dt(version_info.get('createdAt')),
                        'source_filename': f'confluence_{page_id}.md',
                    },
                )

                ticket_refs = list(set(re.findall(r'[A-Z]+-\d+', markdown_content)))
                for ticket_key in ticket_refs:
                    EntityReference.objects.get_or_create(
                        source_type='confluence',
                        source_id=page.id,
                        reference_type='jira_ticket',
                        reference_id=ticket_key,
                        defaults={'extraction_method': 'content_body'},
                    )

                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception:
                error_count += 1

    return {
        'source': 'confluence',
        'space': space_key,
        'created': created_count,
        'updated': updated_count,
        'errors': error_count,
        'total': len(all_pages),
    }


# ── Meetings ──────────────────────────────────────────────────────────────────

def run_meeting_ingest(vtt_content, filename):
    speakers = set()
    for line in vtt_content.split('\n'):
        match = re.match(r'^([A-Za-z\s\']+):', line.strip())
        if match:
            speaker = match.group(1).strip()
            if not re.match(r'^\d', speaker):
                speakers.add(speaker)

    timestamps = re.findall(r'(\d{2}:\d{2}:\d{2})', vtt_content)
    duration_seconds = None
    if timestamps:
        parts = timestamps[-1].split(':')
        duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    title = filename.replace('.vtt', '').replace('_', ' ').title()

    with transaction.atomic():
        meeting, created = Meeting.objects.update_or_create(
            source_filename=filename,
            defaults={
                'title': title,
                'raw_vtt_content': vtt_content,
                'participants': json.dumps(list(speakers)),
                'duration_seconds': duration_seconds,
            },
        )
        ticket_refs = _extract_jira_refs(vtt_content)
        refs_created = _create_entity_refs('meeting', str(meeting.id), ticket_refs, 'vtt_transcript')

    return {
        'source': 'meeting',
        'meeting_id': str(meeting.id),
        'title': title,
        'created': created,
        'participants': len(speakers),
        'duration_seconds': duration_seconds,
        'ticket_references_created': refs_created,
    }
