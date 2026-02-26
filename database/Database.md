# Onboarding AI - Database Documentation

## Overview

The Onboarding AI database stores project knowledge from multiple sources to help new team members understand project history, decisions, and context. It automatically links related information across different platforms.

**Database:** PostgreSQL 18  
**ORM:** Django 4.2  
**Primary Key Type:** UUID (all tables)

---

## Table of Contents

1. [Data Sources](#data-sources)
2. [Schema Diagram](#schema-diagram)
3. [Tables](#tables)
   - [git_commits](#1-git_commits)
   - [git_commit_files](#2-git_commit_files)
   - [meetings](#3-meetings)
   - [jira_tickets](#4-jira_tickets)
   - [confluence_pages](#5-confluence_pages)
   - [entity_references](#6-entity_references)
   - [projects](#7-projects)
   - [project_entities](#8-project_entities)
4. [How Entity References Work](#how-entity-references-work)
5. [Common Queries](#common-queries)
6. [Django Models](#django-models)
7. [Database Views](#database-views)
8. [Data Extraction Scripts](#data-extraction-scripts)
9. [Connection Details](#connection-details)
10. [Environment Variables](#environment-variables)

---

## Data Sources

| Source | Tables | Description |
|--------|--------|-------------|
| GitHub | `git_commits`, `git_commit_files` | Code changes, authors, file modifications |
| Jira | `jira_tickets` | Issues, bugs, tasks, epics, sprints |
| Confluence | `confluence_pages` | Documentation, runbooks, guides |
| Teams/Zoom | `meetings` | Meeting transcripts and AI summaries |

---

## Schema Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PROJECTS                                        │
│  ┌─────────────────┐                                                        │
│  │    projects     │─────────────────────────────────────────┐              │
│  │                 │                                         │              │
│  │ - id            │                                         │              │
│  │ - name          │                                         ▼              │
│  │ - github_repo   │                              ┌─────────────────────┐   │
│  │ - jira_project  │                              │  project_entities   │   │
│  │ - confluence    │                              │                     │   │
│  └─────────────────┘                              │ Links projects to   │   │
│                                                   │ specific entities   │   │
│                                                   └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                       │
│                                                                              │
│  ┌─────────────────┐       ┌─────────────────────┐                          │
│  │   git_commits   │──────▶│  git_commit_files   │                          │
│  │                 │  1:N  │                     │                          │
│  │ - sha           │       │ - filename          │                          │
│  │ - author        │       │ - additions         │                          │
│  │ - message       │       │ - deletions         │                          │
│  │ - related_tickets       │ - status            │                          │
│  └────────┬────────┘       └─────────────────────┘                          │
│           │                                                                  │
│           │         ┌─────────────────┐       ┌─────────────────┐           │
│           │         │    meetings     │       │ confluence_pages│           │
│           │         │                 │       │                 │           │
│           │         │ - title         │       │ - title         │           │
│           │         │ - raw_vtt       │       │ - content       │           │
│           │         │ - summary       │       │ - labels        │           │
│           │         │ - participants  │       │ - space         │           │
│           │         └────────┬────────┘       └────────┬────────┘           │
│           │                  │                         │                     │
│           │                  │                         │                     │
│           ▼                  ▼                         ▼                     │
│  ┌───────────────────────────────────────────────────────────────┐          │
│  │                    entity_references                          │          │
│  │                                                               │          │
│  │  Links ALL sources to Jira tickets (or other entities)        │          │
│  │                                                               │          │
│  │  source_type  │ source_id │ reference_type │ reference_id     │          │
│  │  ─────────────┼───────────┼────────────────┼────────────────  │          │
│  │  commit       │ uuid-1    │ jira_ticket    │ ONBOARD-5        │          │
│  │  meeting      │ uuid-2    │ jira_ticket    │ ONBOARD-5        │          │
│  │  confluence   │ uuid-3    │ jira_ticket    │ ONBOARD-5        │          │
│  └───────────────────────────────────────────────────────────────┘          │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                        │
│  │  jira_tickets   │                                                        │
│  │                 │                                                        │
│  │ - issue_key     │  (e.g., ONBOARD-5)                                     │
│  │ - summary       │                                                        │
│  │ - status        │                                                        │
│  │ - assignee      │                                                        │
│  └─────────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tables

### 1. git_commits

Stores Git commit metadata. **One row per commit.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `sha` | VARCHAR(40) | No | Commit SHA (unique) |
| `author_name` | VARCHAR(255) | No | Author's display name |
| `author_email` | VARCHAR(255) | No | Author's email |
| `commit_date` | TIMESTAMP | No | When commit was made |
| `message` | TEXT | No | Full commit message |
| `related_tickets` | TEXT | Yes | Extracted ticket IDs (e.g., "ONBOARD-1, ONBOARD-2") |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `author_email`, `commit_date`, `sha` (unique)

**Example:**
```
| id     | sha     | author_name | message                        | related_tickets |
|--------|---------|-------------|--------------------------------|-----------------|
| uuid-1 | a1b2c3d | Kousik      | Fix login bug - ONBOARD-5      | ONBOARD-5       |
| uuid-2 | d4e5f6g | Kousik      | Add user authentication        | NULL            |
```

---

### 2. git_commit_files

Stores files changed in each commit. **Multiple rows per commit.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `commit_id` | UUID | No | Foreign key → git_commits |
| `filename` | VARCHAR(500) | No | File path |
| `additions` | INTEGER | No | Lines added |
| `deletions` | INTEGER | No | Lines deleted |
| `status` | VARCHAR(50) | No | added, modified, deleted, renamed |
| `created_at` | TIMESTAMP | No | Record creation time |

**Indexes:** `commit_id`, `filename`  
**Foreign Key:** `commit_id` → `git_commits(id)` ON DELETE CASCADE

**Example:**
```
| id     | commit_id | filename              | additions | deletions | status   |
|--------|-----------|-----------------------|-----------|-----------|----------|
| file-1 | uuid-1    | src/auth/login.py     | 25        | 10        | modified |
| file-2 | uuid-1    | tests/test_login.py   | 50        | 0         | added    |
| file-3 | uuid-2    | src/auth/user.py      | 100       | 0         | added    |
```

**Relationship:**
```
git_commits (1) ───────> (N) git_commit_files

One commit can have MANY files changed
```

---

### 3. meetings

Stores meeting transcripts and AI-generated analysis.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `title` | VARCHAR(500) | Yes | Meeting title |
| `meeting_date` | TIMESTAMP | Yes | When meeting occurred |
| `raw_vtt_content` | TEXT | No | Full VTT transcript |
| `summary` | TEXT | Yes | AI-generated summary (future) |
| `key_decisions` | TEXT | Yes | JSON array of decisions (future) |
| `action_items` | TEXT | Yes | JSON array of action items (future) |
| `participants` | TEXT | Yes | JSON array of speaker names |
| `duration_seconds` | INTEGER | Yes | Meeting length in seconds |
| `source_filename` | VARCHAR(255) | Yes | Original VTT filename |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `meeting_date`

**Note:** `summary`, `key_decisions`, and `action_items` are placeholders for future AI processing.

---

### 4. jira_tickets

Stores Jira ticket information (flat structure).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `issue_key` | VARCHAR(50) | No | Jira key, e.g., "ONBOARD-5" (unique) |
| `issue_type` | VARCHAR(50) | No | Epic, Task, Bug, Story, etc. |
| `summary` | VARCHAR(500) | No | Ticket title |
| `description` | TEXT | Yes | Full description |
| `status` | VARCHAR(50) | No | To Do, In Progress, Done, etc. |
| `priority` | VARCHAR(50) | Yes | High, Medium, Low, etc. |
| `assignee` | VARCHAR(255) | Yes | Assigned person |
| `reporter` | VARCHAR(255) | Yes | Who created the ticket |
| `created_date` | TIMESTAMP | Yes | Ticket creation date |
| `updated_date` | TIMESTAMP | Yes | Last update date |
| `resolved_date` | TIMESTAMP | Yes | Resolution date |
| `labels` | TEXT | Yes | Comma-separated labels |
| `epic_link` | VARCHAR(50) | Yes | Parent epic issue key |
| `sprint` | VARCHAR(100) | Yes | Sprint name |
| `story_points` | INTEGER | Yes | Story points estimate |
| `comments` | TEXT | Yes | JSON array of comments |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `issue_key` (unique), `status`, `assignee`, `epic_link`, `created_date`

---

### 5. confluence_pages

Stores Confluence documentation pages.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `title` | VARCHAR(500) | No | Page title |
| `space` | VARCHAR(255) | Yes | Confluence space name |
| `author` | VARCHAR(255) | Yes | Page author |
| `content` | TEXT | No | Full page content (Markdown format) |
| `labels` | TEXT[] | Yes | PostgreSQL array of labels |
| `version` | INTEGER | No | Page version number |
| `page_created_date` | TIMESTAMP | Yes | Original creation date |
| `page_updated_date` | TIMESTAMP | Yes | Last update date |
| `source_filename` | VARCHAR(255) | Yes | Original filename |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `space`, `author`, `labels` (GIN index for array search)

---

### 6. entity_references

**The most important table!** Links entities across different sources. This is the core table that connects everything.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `source_type` | VARCHAR(50) | No | commit, meeting, jira_ticket, confluence |
| `source_id` | UUID | No | ID of the source entity |
| `reference_type` | VARCHAR(50) | No | Type being referenced (usually jira_ticket) |
| `reference_id` | VARCHAR(100) | No | Referenced ID (e.g., "ONBOARD-5") |
| `extraction_method` | VARCHAR(50) | Yes | How reference was found |
| `created_at` | TIMESTAMP | No | Record creation time |

**Unique Constraint:** `(source_type, source_id, reference_type, reference_id)`  
**Indexes:** `(source_type, source_id)`, `(reference_type, reference_id)`

**Extraction Methods:**
| Method | Description |
|--------|-------------|
| `commit_message` | Found in git commit message |
| `vtt_transcript` | Found in meeting transcript |
| `content_body` | Found in Confluence page content |
| `epic_link` | From Jira epic_link field |

---

### 7. projects

Groups related tickets, commits, meetings, and pages into a single project/feature.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `name` | VARCHAR(255) | No | Project name |
| `description` | TEXT | Yes | Project description |
| `status` | VARCHAR(50) | No | active, completed, on_hold, cancelled |
| `epic_key` | VARCHAR(50) | Yes | Main Jira epic (e.g., "ONBOARD-1") |
| `jira_project_key` | VARCHAR(20) | Yes | Jira project key (e.g., "ONBOARD") |
| `github_repo` | VARCHAR(255) | Yes | GitHub repository (e.g., "nkousik18/LoanQA-MLOps") |
| `confluence_space_key` | VARCHAR(50) | Yes | Confluence space key (e.g., "ONBOARD") |
| `start_date` | DATE | Yes | Project start date |
| `target_end_date` | DATE | Yes | Planned end date |
| `actual_end_date` | DATE | Yes | Actual completion date |
| `owner` | VARCHAR(255) | Yes | Project owner |
| `team_members` | TEXT | Yes | JSON array of team member names |
| `tags` | TEXT[] | Yes | PostgreSQL array of tags |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `status`, `epic_key`, `github_repo`, `tags` (GIN index)

---

### 8. project_entities

Links projects to specific entities (for manual or automatic linking).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `project_id` | UUID | No | Foreign key → projects |
| `entity_type` | VARCHAR(50) | No | commit, meeting, jira_ticket, confluence |
| `entity_id` | UUID | No | ID of the linked entity |
| `added_manually` | BOOLEAN | No | true if manually linked, false if auto-detected |
| `created_at` | TIMESTAMP | No | Record creation time |

**Unique Constraint:** `(project_id, entity_type, entity_id)`  
**Foreign Key:** `project_id` → `projects(id)` ON DELETE CASCADE

---

## How Entity References Work

### The Automatic Linking Process

When data is ingested, the system automatically scans for Jira ticket IDs (pattern: `[A-Z]+-\d+`) and creates links.

### Example Flow

**Step 1:** You make a commit with this message:
```
Fix login validation bug

Fixes ONBOARD-5, related to ONBOARD-3
```

**Step 2:** The extraction script:
1. Saves the commit to `git_commits`
2. Saves changed files to `git_commit_files`
3. Scans the message, finds: `ONBOARD-5`, `ONBOARD-3`
4. Creates entries in `entity_references`:

```
| source_type | source_id    | reference_type | reference_id | extraction_method |
|-------------|--------------|----------------|--------------|-------------------|
| commit      | (commit uuid)| jira_ticket    | ONBOARD-5    | commit_message    |
| commit      | (commit uuid)| jira_ticket    | ONBOARD-3    | commit_message    |
```

**Step 3:** Same happens for Confluence and Meetings:

```
| source_type | source_id   | reference_type | reference_id | extraction_method |
|-------------|-------------|----------------|--------------|-------------------|
| confluence  | (page uuid) | jira_ticket    | ONBOARD-5    | content_body      |
| meeting     | (meet uuid) | jira_ticket    | ONBOARD-5    | vtt_transcript    |
```

### The Power: Cross-Source Queries

Now you can answer: **"Show me everything related to ONBOARD-5"**

```
                    ONBOARD-5 (Jira Ticket)
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Commits   │  │  Meetings  │  │ Confluence │
    │            │  │            │  │   Pages    │
    │ - Fix bug  │  │ - Discussed│  │ - Runbook  │
    │ - Add test │  │   the bug  │  │ - API docs │
    └────────────┘  └────────────┘  └────────────┘
```

---

## Common Queries

### Find everything related to a ticket

```sql
-- Get all entity references for ONBOARD-5
SELECT * FROM entity_references 
WHERE reference_type = 'jira_ticket' 
AND reference_id = 'ONBOARD-5';
```

### Get commits that mention a ticket

```sql
SELECT c.* FROM git_commits c
JOIN entity_references er ON c.id = er.source_id
WHERE er.source_type = 'commit'
AND er.reference_type = 'jira_ticket'
AND er.reference_id = 'ONBOARD-5';
```

### Get files changed for a ticket

```sql
SELECT cf.* FROM git_commit_files cf
JOIN git_commits c ON cf.commit_id = c.id
JOIN entity_references er ON c.id = er.source_id
WHERE er.source_type = 'commit'
AND er.reference_type = 'jira_ticket'
AND er.reference_id = 'ONBOARD-5';
```

### Get timeline for a project

```sql
SELECT * FROM unified_timeline
WHERE event_date > '2026-01-01'
ORDER BY event_date DESC;
```

### Search Confluence by label

```sql
-- Find all runbooks
SELECT * FROM confluence_pages 
WHERE 'runbook' = ANY(labels);

-- Find pages with multiple labels
SELECT * FROM confluence_pages 
WHERE labels @> ARRAY['api', 'documentation'];
```

### Get all open tickets

```sql
SELECT * FROM jira_tickets 
WHERE status NOT IN ('Done', 'Closed')
ORDER BY created_date DESC;
```

### Get activity by a person

```sql
-- Commits by author
SELECT * FROM git_commits WHERE author_name = 'Kousik';

-- Assigned tickets
SELECT * FROM jira_tickets WHERE assignee = 'Ash ketchum';

-- Confluence pages by author
SELECT * FROM confluence_pages WHERE author LIKE '%kousik%';
```

---

## Django Models

**Location:** `Onboarding_AI/database/knowledge_base/models.py`

All models use `managed = False` since tables were created directly in PostgreSQL.

```python
from knowledge_base.models import (
    GitCommit,
    GitCommitFile,
    Meeting,
    JiraTicket,
    ConfluencePage,
    EntityReference,
    Project,
    ProjectEntity
)

# Example: Find commits for a ticket
refs = EntityReference.objects.filter(
    reference_type='jira_ticket',
    reference_id='ONBOARD-5',
    source_type='commit'
)
commit_ids = refs.values_list('source_id', flat=True)
commits = GitCommit.objects.filter(id__in=commit_ids)

# Example: Get files for a commit
commit = GitCommit.objects.get(sha='a1b2c3d')
files = commit.files.all()  # Uses related_name='files'
```

---

## Database Views

### unified_timeline

Combines all entities into a single chronological view.

| Column | Description |
|--------|-------------|
| `entity_type` | commit, meeting, jira_ticket, confluence |
| `entity_id` | UUID of the entity |
| `event_date` | When the event occurred |
| `title` | Title/summary of the event |
| `actor` | Person responsible |
| `context` | Additional context |

```sql
-- View definition
CREATE VIEW unified_timeline AS
SELECT 
    'commit' as entity_type,
    id as entity_id,
    commit_date as event_date,
    message as title,
    author_name as actor,
    related_tickets as context
FROM git_commits
UNION ALL
SELECT 
    'meeting' as entity_type,
    id as entity_id,
    meeting_date as event_date,
    title,
    NULL as actor,
    participants as context
FROM meetings
UNION ALL
SELECT 
    'jira_ticket' as entity_type,
    id as entity_id,
    created_date as event_date,
    summary as title,
    assignee as actor,
    issue_key as context
FROM jira_tickets
UNION ALL
SELECT 
    'confluence' as entity_type,
    id as entity_id,
    page_created_date as event_date,
    title,
    author as actor,
    space as context
FROM confluence_pages
ORDER BY event_date DESC;
```

---

## Data Extraction Scripts

**Location:** `Onboarding_AI/database/scripts/`

| Script | Source | Command |
|--------|--------|---------|
| `extract_github.py` | GitHub API | `python scripts/extract_github.py` |
| `extract_confluence.py` | Confluence API | `python scripts/extract_confluence.py` |
| `extract_jira.py` | Jira API | `python scripts/extract_jira.py` |

### What Each Script Does

1. **Fetches data** from the API
2. **Saves to database** (creates or updates records)
3. **Extracts ticket references** (scans for patterns like `ONBOARD-5`)
4. **Creates entity_references** links automatically

---

## Connection Details

### Development

```
Host: localhost
Port: 5432
Database: project_knowledge
User: postgres
```

### Connecting via Command Line

```bash
/Library/PostgreSQL/18/bin/psql -U postgres -d project_knowledge
```

### Useful psql Commands

| Command | Description |
|---------|-------------|
| `\dt` | List all tables |
| `\d tablename` | Describe table structure |
| `\dv` | List all views |
| `\q` | Quit |

---

## Environment Variables

Create a `.env` file in the `database/` folder:

```bash
# Database
DB_NAME=project_knowledge
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
DEBUG=True
SECRET_KEY=your-secret-key

# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_OWNER=nkousik18
GITHUB_REPO=LoanQA-MLOps
GITHUB_MAX_COMMITS=100

# Jira
JIRA_DOMAIN=onboardingaii.atlassian.net
JIRA_EMAIL=ash.ketchum3847@gmail.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=ONBOARD
JIRA_MAX_ISSUES=500

# Confluence
CONFLUENCE_DOMAIN=onboardingaii.atlassian.net
CONFLUENCE_EMAIL=ash.ketchum3847@gmail.com
CONFLUENCE_API_TOKEN=your-confluence-api-token
CONFLUENCE_SPACE_KEY=ONBOARD
CONFLUENCE_SPACE_ID=1474564
```

---

## Maintenance

### Automatic Timestamps

All tables have triggers that automatically update `updated_at` on row changes.

### Indexes

Indexes are created for common query patterns:
- Filtering by date
- Filtering by author/assignee
- Searching by ticket key
- Array searches on labels (GIN index)

### Re-running Extraction

Scripts use `update_or_create`, so running them multiple times is safe:
- New records are created
- Existing records are updated
- No duplicates are created

---

## File Structure

```
Onboarding_AI/
└── database/
    ├── manage.py                 # Django CLI
    ├── requirements.txt          # Python dependencies
    ├── .env                      # Environment variables (create from .env.example)
    ├── .env.example              # Template
    ├── DATABASE.md               # This file
    ├── config/
    │   ├── settings.py           # Django settings
    │   ├── urls.py               # URL routing
    │   └── wsgi.py               # WSGI application
    ├── knowledge_base/
    │   ├── models.py             # Database models
    │   ├── admin.py              # Admin interface config
    │   └── management/commands/
    │       └── ingest_data.py    # Legacy ingestion command
    ├── scripts/
    │   ├── extract_github.py     # GitHub extraction
    │   ├── extract_confluence.py # Confluence extraction
    │   └── extract_jira.py       # Jira extraction
    ├── sql/
    │   └── 001_create_schema.sql # Original SQL schema
    └── docs/
        ├── BACKEND_DEVELOPER_GUIDE.md
        └── DATA_SOURCE_SETUP_GUIDE.md
```

---

## Quick Reference

### Start Django Server
```bash
cd ~/Desktop/Onboarding_AI/database
source ../venv/bin/activate
python manage.py runserver
```

### Access Admin
http://127.0.0.1:8000/admin/

### Run Extractions
```bash
python scripts/extract_github.py
python scripts/extract_confluence.py
python scripts/extract_jira.py
```

### Django Shell
```bash
python manage.py shell
```

---

*Last updated: February 2026*