# Onboarding AI - Database Documentation

## Overview

The Onboarding AI database stores project knowledge from multiple sources to help new team members understand project history, decisions, and context. It automatically links related information across different platforms.

**Database:** PostgreSQL 16 (Hosted on Render)  
**ORM:** Django 4.2  
**Primary Key Type:** UUID (all tables)  
**Total Tables:** 11

---

## Table of Contents

1. [Data Sources](#data-sources)
2. [Schema Diagram](#schema-diagram)
3. [Tables](#tables)
   - [employees](#1-employees)
   - [git_commits](#2-git_commits)
   - [git_commit_files](#3-git_commit_files)
   - [meetings](#4-meetings)
   - [jira_tickets](#5-jira_tickets)
   - [confluence_pages](#6-confluence_pages)
   - [entity_references](#7-entity_references)
   - [projects](#8-projects)
   - [project_entities](#9-project_entities)
   - [sprints](#10-sprints)
   - [sprint_tickets](#11-sprint_tickets)
4. [How Entity References Work](#how-entity-references-work)
5. [How Sprints Work](#how-sprints-work)
6. [Common Queries](#common-queries)
7. [Django Models](#django-models)
8. [Database Views](#database-views)
9. [Data Ingestion](#data-ingestion)
10. [Connection Details](#connection-details)

---

## Data Sources

| Source | Tables | Description |
|--------|--------|-------------|
| Team | `employees` | Team members and their roles |
| GitHub | `git_commits`, `git_commit_files` | Code changes, authors, file modifications |
| Jira | `jira_tickets` | Issues, bugs, tasks, epics |
| Confluence | `confluence_pages` | Documentation, runbooks, guides |
| Teams/Zoom | `meetings` | Meeting transcripts (VTT format) |
| Project Management | `projects`, `sprints`, `sprint_tickets` | Project and sprint tracking |

---

## Schema Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TEAM                                            │
│  ┌─────────────────┐                                                        │
│  │   employees     │                                                        │
│  │                 │                                                        │
│  │ - name          │◄──────── Linked via name/email to commits, tickets     │
│  │ - email         │                                                        │
│  │ - role          │                                                        │
│  │ - department    │                                                        │
│  └─────────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROJECTS & SPRINTS                                   │
│                                                                              │
│  ┌─────────────────┐         ┌─────────────────┐         ┌───────────────┐  │
│  │    projects     │────────▶│     sprints     │────────▶│sprint_tickets │  │
│  │                 │   1:N   │                 │   1:N   │               │  │
│  │ - name          │         │ - sprint_number │         │ - sprint_id   │  │
│  │ - github_repo   │         │ - name          │         │ - ticket_id   │  │
│  │ - jira_project  │         │ - start_date    │         │ - added_date  │  │
│  │ - owner         │         │ - end_date      │         └───────┬───────┘  │
│  └────────┬────────┘         │ - goal          │                 │          │
│           │                  │ - status        │                 │          │
│           │                  └─────────────────┘                 │          │
│           ▼                                                      │          │
│  ┌─────────────────┐                                             │          │
│  │project_entities │                                             │          │
│  │                 │                                             │          │
│  │ Links projects  │                                             │          │
│  │ to any entity   │                                             │          │
│  └─────────────────┘                                             │          │
└──────────────────────────────────────────────────────────────────┼──────────┘
                                                                   │
┌──────────────────────────────────────────────────────────────────┼──────────┐
│                           DATA SOURCES                           │          │
│                                                                  │          │
│  ┌─────────────────┐       ┌─────────────────────┐               │          │
│  │   git_commits   │──────▶│  git_commit_files   │               │          │
│  │                 │  1:N  │                     │               │          │
│  │ - sha           │       │ - filename          │               │          │
│  │ - author        │       │ - additions         │               │          │
│  │ - message       │       │ - deletions         │               │          │
│  └────────┬────────┘       └─────────────────────┘               │          │
│           │                                                      │          │
│           │         ┌─────────────────┐       ┌─────────────────┐│          │
│           │         │    meetings     │       │ confluence_pages││          │
│           │         │                 │       │                 ││          │
│           │         │ - title         │       │ - title         ││          │
│           │         │ - raw_vtt       │       │ - content       ││          │
│           │         │ - participants  │       │ - labels        ││          │
│           │         └────────┬────────┘       └────────┬────────┘│          │
│           │                  │                         │         │          │
│           ▼                  ▼                         ▼         ▼          │
│  ┌───────────────────────────────────────────────────────────────────┐      │
│  │                    entity_references                              │      │
│  │                                                                   │      │
│  │  Links ALL sources to Jira tickets (or other entities)            │      │
│  │                                                                   │      │
│  │  source_type  │ source_id │ reference_type │ reference_id         │      │
│  │  ─────────────┼───────────┼────────────────┼────────────────      │      │
│  │  commit       │ uuid-1    │ jira_ticket    │ ONBOARD-11           │      │
│  │  meeting      │ uuid-2    │ jira_ticket    │ ONBOARD-11           │      │
│  │  confluence   │ uuid-3    │ jira_ticket    │ ONBOARD-11           │      │
│  └───────────────────────────────────────────────────────────────────┘      │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                        │
│  │  jira_tickets   │◄────────────────────────────────────────────────────────
│  │                 │                                                        │
│  │ - issue_key     │  (e.g., ONBOARD-11)                                    │
│  │ - summary       │                                                        │
│  │ - status        │                                                        │
│  │ - assignee      │                                                        │
│  └─────────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tables

### 1. employees

Stores team member information. Populated from Jira assignees, Git authors, and CSV imports.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `name` | VARCHAR(255) | No | Employee name (unique) |
| `email` | VARCHAR(255) | Yes | Email address |
| `role` | VARCHAR(100) | Yes | Job role (e.g., "Backend Developer") |
| `department` | VARCHAR(100) | Yes | Department (e.g., "Engineering") |
| `source` | VARCHAR(50) | Yes | Where data came from: jira, git, csv |
| `jira_account_id` | VARCHAR(255) | Yes | Atlassian account ID |
| `github_username` | VARCHAR(255) | Yes | GitHub username |
| `is_active` | BOOLEAN | No | Active employee flag (default: true) |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `name` (unique), `department`

**Example:**
```
| name            | email                          | role              | department  |
|-----------------|--------------------------------|-------------------|-------------|
| Sarah Chen      | sarah.chen@meridiantech.com    | Tech Lead         | Engineering |
| Marcus Thompson | marcus.thompson@meridiantech.com| Backend Developer | Engineering |
| James O'Brien   | james.obrien@meridiantech.com  | Junior Developer  | Engineering |
```

---

### 2. git_commits

Stores Git commit metadata. **One row per commit.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `sha` | VARCHAR(40) | No | Commit SHA (unique) |
| `author_name` | VARCHAR(255) | No | Author's display name |
| `author_email` | VARCHAR(255) | No | Author's email |
| `commit_date` | TIMESTAMP | No | When commit was made |
| `message` | TEXT | No | Full commit message |
| `related_tickets` | TEXT | Yes | Extracted ticket IDs (e.g., "ONBOARD-11, ONBOARD-12") |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `sha` (unique), `author_email`, `commit_date`

---

### 3. git_commit_files

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

---

### 4. meetings

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

---

### 5. jira_tickets

Stores Jira ticket information.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `issue_key` | VARCHAR(50) | No | Jira key, e.g., "ONBOARD-11" (unique) |
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
| `sprint` | VARCHAR(100) | Yes | Sprint name (text field) |
| `story_points` | INTEGER | Yes | Story points estimate |
| `comments` | TEXT | Yes | JSON array of comments |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `issue_key` (unique), `status`, `assignee`, `epic_link`, `created_date`

---

### 6. confluence_pages

Stores Confluence documentation pages (content as Markdown).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `title` | VARCHAR(500) | No | Page title |
| `space` | VARCHAR(255) | Yes | Confluence space key |
| `author` | VARCHAR(255) | Yes | Page author name |
| `content` | TEXT | No | Page content (Markdown) |
| `labels` | TEXT[] | Yes | Array of labels |
| `version` | INTEGER | No | Page version number |
| `page_created_date` | TIMESTAMP | Yes | Page creation date |
| `page_updated_date` | TIMESTAMP | Yes | Page last update date |
| `source_filename` | VARCHAR(255) | Yes | Source filename |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `space`, `author`, `labels` (GIN)

---

### 7. entity_references

Links entities across different sources. **The core linking table.**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `source_type` | VARCHAR(50) | No | commit, meeting, confluence, jira_ticket |
| `source_id` | UUID | No | ID of the source entity |
| `reference_type` | VARCHAR(50) | No | Type of reference (usually "jira_ticket") |
| `reference_id` | VARCHAR(100) | No | Referenced entity ID (e.g., "ONBOARD-11") |
| `extraction_method` | VARCHAR(50) | Yes | How it was extracted |
| `created_at` | TIMESTAMP | No | Record creation time |

**Indexes:** `(source_type, source_id)`, `(reference_type, reference_id)`  
**Unique Constraint:** `(source_type, source_id, reference_type, reference_id)`

---

### 8. projects

Groups related work under a single project.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `name` | VARCHAR(255) | No | Project name |
| `description` | TEXT | Yes | Project description |
| `status` | VARCHAR(50) | No | active, completed, on_hold |
| `epic_key` | VARCHAR(50) | Yes | Main epic issue key |
| `jira_project_key` | VARCHAR(20) | Yes | Jira project key (e.g., "ONBOARD") |
| `github_repo` | VARCHAR(255) | Yes | GitHub repository |
| `confluence_space_key` | VARCHAR(50) | Yes | Confluence space |
| `start_date` | DATE | Yes | Project start date |
| `target_end_date` | DATE | Yes | Target completion date |
| `actual_end_date` | DATE | Yes | Actual completion date |
| `owner` | VARCHAR(255) | Yes | Project owner |
| `team_members` | TEXT | Yes | JSON array of team members |
| `tags` | TEXT[] | Yes | Array of tags |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `status`, `epic_key`, `github_repo`, `tags` (GIN)

---

### 9. project_entities

Links specific entities to projects.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `project_id` | UUID | No | Foreign key → projects |
| `entity_type` | VARCHAR(50) | No | commit, meeting, jira_ticket, etc. |
| `entity_id` | UUID | No | ID of the linked entity |
| `added_manually` | BOOLEAN | No | Was this manually added? |
| `created_at` | TIMESTAMP | No | Record creation time |

**Foreign Key:** `project_id` → `projects(id)` ON DELETE CASCADE

---

### 10. sprints

Stores sprint information linked to projects.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `sprint_number` | INTEGER | No | Sprint number (1, 2, 3...) |
| `name` | VARCHAR(255) | No | Sprint name (e.g., "Sprint 1 - Foundation") |
| `start_date` | DATE | No | Sprint start date |
| `end_date` | DATE | No | Sprint end date |
| `goal` | TEXT | Yes | Sprint goal/objective |
| `project_id` | UUID | Yes | Foreign key → projects |
| `status` | VARCHAR(50) | No | planned, active, completed |
| `created_at` | TIMESTAMP | No | Record creation time |
| `updated_at` | TIMESTAMP | No | Record last update time |

**Indexes:** `project_id`, `status`, `start_date`  
**Foreign Key:** `project_id` → `projects(id)` ON DELETE CASCADE  
**Unique Constraint:** `(sprint_number, project_id)`

**Example:**
```
| sprint_number | name                    | start_date | end_date   | status    |
|---------------|-------------------------|------------|------------|-----------|
| 1             | Sprint 1 - Foundation   | 2026-01-05 | 2026-01-16 | completed |
| 2             | Sprint 2 - Core Features| 2026-01-19 | 2026-01-30 | completed |
```

---

### 11. sprint_tickets

Links sprints to Jira tickets.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `sprint_id` | UUID | No | Foreign key → sprints |
| `ticket_id` | UUID | No | Foreign key → jira_tickets |
| `added_date` | DATE | Yes | When ticket was added to sprint |
| `created_at` | TIMESTAMP | No | Record creation time |

**Indexes:** `sprint_id`, `ticket_id`  
**Foreign Keys:** 
- `sprint_id` → `sprints(id)` ON DELETE CASCADE
- `ticket_id` → `jira_tickets(id)` ON DELETE CASCADE  
**Unique Constraint:** `(sprint_id, ticket_id)`

---

## How Entity References Work

The `entity_references` table automatically links data across sources when ticket IDs are mentioned.

**Example Flow:**

```
Commit message: "feat: add login page - ONBOARD-15"
                                         │
                                         ▼
                            Script extracts "ONBOARD-15"
                                         │
                                         ▼
                            Creates entity_reference:
                            ┌─────────────────────────────────┐
                            │ source_type: commit             │
                            │ source_id: (commit UUID)        │
                            │ reference_type: jira_ticket     │
                            │ reference_id: ONBOARD-15        │
                            └─────────────────────────────────┘
```

**Query: "Show everything related to ONBOARD-15"**

```sql
SELECT source_type, source_id 
FROM entity_references 
WHERE reference_id = 'ONBOARD-15';
```

Returns commits, meetings, and confluence pages that mention this ticket.

---

## How Sprints Work

Sprints are linked to projects and contain multiple tickets via the `sprint_tickets` table.

```
┌─────────────┐         ┌─────────────┐         ┌───────────────┐
│  projects   │────────▶│   sprints   │────────▶│ sprint_tickets│
│             │   1:N   │             │   1:N   │               │
│ Employee    │         │ Sprint 1    │         │ ONBOARD-11    │
│ Onboarding  │         │ Sprint 2    │         │ ONBOARD-12    │
│ Portal      │         │             │         │ ONBOARD-13    │
└─────────────┘         └─────────────┘         └───────┬───────┘
                                                        │
                                                        ▼
                                                ┌───────────────┐
                                                │ jira_tickets  │
                                                │               │
                                                │ ONBOARD-11    │
                                                │ ONBOARD-12    │
                                                │ ONBOARD-13    │
                                                └───────────────┘
```

**Query: "Show all tickets in Sprint 1"**

```sql
SELECT j.issue_key, j.summary, j.status, j.assignee
FROM sprints s
JOIN sprint_tickets st ON s.id = st.sprint_id
JOIN jira_tickets j ON st.ticket_id = j.id
WHERE s.sprint_number = 1
ORDER BY j.issue_key;
```

---

## Common Queries

### Count All Records

```sql
SELECT 'employees' as tbl, COUNT(*) FROM employees
UNION ALL SELECT 'commits', COUNT(*) FROM git_commits
UNION ALL SELECT 'files', COUNT(*) FROM git_commit_files
UNION ALL SELECT 'tickets', COUNT(*) FROM jira_tickets
UNION ALL SELECT 'pages', COUNT(*) FROM confluence_pages
UNION ALL SELECT 'meetings', COUNT(*) FROM meetings
UNION ALL SELECT 'sprints', COUNT(*) FROM sprints
UNION ALL SELECT 'references', COUNT(*) FROM entity_references;
```

### Find Everything Related to a Ticket

```sql
SELECT source_type, source_id, extraction_method
FROM entity_references
WHERE reference_id = 'ONBOARD-11';
```

### Get Commits for a Ticket

```sql
SELECT c.sha, c.author_name, c.message, c.commit_date
FROM git_commits c
JOIN entity_references er ON c.id = er.source_id
WHERE er.source_type = 'commit'
  AND er.reference_id = 'ONBOARD-11'
ORDER BY c.commit_date;
```

### View Sprint with Tickets

```sql
SELECT s.name, s.start_date, s.end_date, 
       j.issue_key, j.summary, j.status, j.assignee
FROM sprints s
JOIN sprint_tickets st ON s.id = st.sprint_id
JOIN jira_tickets j ON st.ticket_id = j.id
ORDER BY s.sprint_number, j.issue_key;
```

### Get Employee Activity

```sql
-- Commits by employee
SELECT c.sha, c.message, c.commit_date
FROM git_commits c
JOIN employees e ON c.author_email = e.email
WHERE e.name = 'Marcus Thompson'
ORDER BY c.commit_date DESC;

-- Tickets assigned to employee
SELECT issue_key, summary, status
FROM jira_tickets
WHERE assignee = 'Marcus Thompson';
```

### View Project Timeline

```sql
SELECT * FROM unified_timeline
ORDER BY event_date DESC
LIMIT 20;
```

---

## Django Models

### Key Models

```python
from knowledge_base.models import *

# Employees
Employee.objects.all()
Employee.objects.filter(department='Engineering')

# Commits
GitCommit.objects.filter(author_name='Marcus Thompson')
commit = GitCommit.objects.first()
commit.files.all()  # Get files changed

# Tickets
JiraTicket.objects.filter(status='Done')
JiraTicket.objects.filter(assignee='Sarah Chen')

# Sprints
Sprint.objects.all()
sprint = Sprint.objects.get(sprint_number=1)
for st in sprint.sprint_tickets.all():
    print(st.ticket.issue_key)

# Entity References
EntityReference.objects.filter(reference_id='ONBOARD-11')
```

---

## Database Views

### unified_timeline

Combines all entities into a single chronological view.

```sql
SELECT * FROM unified_timeline ORDER BY event_date DESC LIMIT 10;
```

| Column | Description |
|--------|-------------|
| `entity_type` | commit, meeting, jira_ticket, confluence |
| `entity_id` | UUID of the entity |
| `event_date` | When the event occurred |
| `title` | Title/summary |
| `actor` | Person responsible |
| `context` | Additional context |

---

## Data Ingestion

### Available Commands

```bash
python manage.py ingest_data --employees /path/to/employees.csv
python manage.py ingest_data --projects /path/to/projects.csv
python manage.py ingest_data --jira /path/to/jira_tickets.csv
python manage.py ingest_data --sprints /path/to/sprints.csv
python manage.py ingest_data --sprint-tickets /path/to/sprint_tickets.csv
python manage.py ingest_data --commits /path/to/git_commits.json
python manage.py ingest_data --meetings /path/to/meeting.vtt
python manage.py ingest_data --confluence /path/to/page.md
```

### Ingestion Order (Important!)

```
1. employees      (no dependencies)
2. projects       (no dependencies)
3. jira tickets   (no dependencies)
4. sprints        (requires projects)
5. sprint-tickets (requires sprints + tickets)
6. commits        (no dependencies)
7. meetings       (no dependencies)
8. confluence     (no dependencies)
```

---

## Connection Details

### Render Cloud (Production)

| Field | Value |
|-------|-------|
| Host | `dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com` |
| Port | `5432` |
| Database | `project_knowledge` |
| Username | `onboarding_user` |

### Connection String

```
postgresql://onboarding_user:PASSWORD@dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com/project_knowledge
```

### Connect via psql

```bash
psql "postgresql://onboarding_user:PASSWORD@dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com/project_knowledge"
```

### Useful psql Commands

| Command | Description |
|---------|-------------|
| `\dt` | List all tables |
| `\d tablename` | Describe table |
| `\dv` | List views |
| `\q` | Quit |

---

## Environment Variables

```bash
# Database (Render)
DB_NAME=project_knowledge
DB_USER=onboarding_user
DB_PASSWORD=your-password
DB_HOST=dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com
DB_PORT=5432

# Django
DEBUG=True
SECRET_KEY=your-secret-key

# GitHub (for API extraction)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_OWNER=your-org
GITHUB_REPO=your-repo

# Jira & Confluence
JIRA_DOMAIN=your-domain.atlassian.net
JIRA_EMAIL=your-email
JIRA_API_TOKEN=your-token
JIRA_PROJECT_KEY=ONBOARD
CONFLUENCE_SPACE_KEY=ONBOARD
```

---

## Quick Reference

### Start Server
```bash
cd ~/Desktop/Onboarding_AI/database
source ../venv/bin/activate
python manage.py runserver
```

### Admin Panel
http://127.0.0.1:8000/admin/

### Django Shell
```bash
python manage.py shell
```

### Reset Database
```sql
DROP VIEW IF EXISTS unified_timeline CASCADE;
DROP TABLE IF EXISTS sprint_tickets, sprints, project_entities, projects,
    entity_references, git_commit_files, git_commits, meetings,
    jira_tickets, confluence_pages, employees CASCADE;
```

---

*Last updated: February 2026*