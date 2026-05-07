# Onboarding AI - Backend Developer Guide

A practical guide for backend developers working on the Onboarding AI project.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Environment Setup](#environment-setup)
4. [Database Setup](#database-setup)
5. [Running the Application](#running-the-application)
6. [Data Ingestion](#data-ingestion)
7. [Data Extraction Scripts](#data-extraction-scripts)
8. [Working with the Database](#working-with-the-database)
9. [Django Admin](#django-admin)
10. [API Credentials](#api-credentials)
11. [Common Tasks](#common-tasks)
12. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Navigate to project
cd ~/Desktop/Onboarding_AI/database

# 2. Activate virtual environment
source ../venv/bin/activate

# 3. Verify setup
python manage.py check

# 4. Run server
python manage.py runserver

# 5. Access admin at http://127.0.0.1:8000/admin/
```

---

## Project Structure

```
Onboarding_AI/
├── venv/                         # Python virtual environment
└── database/
    ├── manage.py                 # Django CLI entry point
    ├── requirements.txt          # Python dependencies
    ├── .env                      # Environment variables (DO NOT COMMIT)
    ├── .env.example              # Environment template
    ├── .gitignore
    ├── DATABASE.md               # Database documentation
    ├── DEVELOPER_GUIDE.md        # This file
    │
    ├── config/                   # Django project settings
    │   ├── __init__.py
    │   ├── settings.py           # Main settings file
    │   ├── urls.py               # URL routing
    │   └── wsgi.py               # WSGI application
    │
    ├── knowledge_base/           # Main Django app
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── models.py             # Database models (11 models)
    │   ├── admin.py              # Admin interface configuration
    │   └── management/
    │       └── commands/
    │           └── ingest_data.py    # Data ingestion command
    │
    ├── scripts/                  # Data extraction scripts (API-based)
    │   ├── extract_github.py     # Fetch commits from GitHub API
    │   ├── extract_confluence.py # Fetch pages from Confluence API
    │   └── extract_jira.py       # Fetch tickets from Jira API
    │
    ├── sql/
    │   ├── 000_complete_schema.sql   # Complete database schema
    │   └── 001_create_sprints_tables.sql
    │
    └── docs/
        ├── BACKEND_DEVELOPER_GUIDE.md
        ├── DB_CONNECTION_GUIDE.md
        ├── EMPLOYEES_TABLE.md
        └── DATA_SOURCE_SETUP_GUIDE.md
```

---

## Environment Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (we use PostgreSQL 16 on Render)
- Git

### Step 1: Clone and Navigate

```bash
git clone https://github.com/preetishreddy/ex-cdi.git
cd ex-cdi/database
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv ../venv
source ../venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

**Required variables:**

```bash
# Database (Render Cloud)
DB_NAME=project_knowledge
DB_USER=onboarding_user
DB_PASSWORD=T9hSACQXUiLLlJfNcxM1hBEwwRWYAnvQ
DB_HOST=dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com
DB_PORT=5432

# Django
DEBUG=True
SECRET_KEY=your-secret-key-here

# GitHub (for API extraction)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_OWNER=your-org
GITHUB_REPO=your-repo

# Jira & Confluence
JIRA_DOMAIN=your-domain.atlassian.net
JIRA_EMAIL=your-email@gmail.com
JIRA_API_TOKEN=your-atlassian-api-token
JIRA_PROJECT_KEY=ONBOARD

CONFLUENCE_DOMAIN=your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@gmail.com
CONFLUENCE_API_TOKEN=your-atlassian-api-token
CONFLUENCE_SPACE_KEY=ONBOARD
CONFLUENCE_SPACE_ID=1474564
```

### Step 5: Verify Database Connection

```bash
python manage.py check
```

---

## Database Setup

### Database Location

The database is hosted on **Render** (cloud):

| Field | Value |
|-------|-------|
| Host | `dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com` |
| Port | `5432` |
| Database | `project_knowledge` |
| Username | `onboarding_user` |

### Connect to Database

```bash
psql "postgresql://onboarding_user:T9hSACQXUiLLlJfNcxM1hBEwwRWYAnvQ@dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com/project_knowledge"
```

### Database Tables (11 Tables)

| Table | Description |
|-------|-------------|
| `employees` | Team members |
| `git_commits` | Git commit metadata |
| `git_commit_files` | Files changed per commit |
| `jira_tickets` | Jira issues |
| `confluence_pages` | Documentation pages |
| `meetings` | Meeting transcripts (VTT) |
| `entity_references` | Cross-links between entities |
| `projects` | Project groupings |
| `project_entities` | Links entities to projects |
| `sprints` | Sprint information |
| `sprint_tickets` | Links sprints to tickets |

### Reset Database (If Needed)

```sql
-- Drop all tables
DROP VIEW IF EXISTS unified_timeline CASCADE;
DROP TABLE IF EXISTS sprint_tickets CASCADE;
DROP TABLE IF EXISTS sprints CASCADE;
DROP TABLE IF EXISTS project_entities CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS entity_references CASCADE;
DROP TABLE IF EXISTS git_commit_files CASCADE;
DROP TABLE IF EXISTS git_commits CASCADE;
DROP TABLE IF EXISTS meetings CASCADE;
DROP TABLE IF EXISTS jira_tickets CASCADE;
DROP TABLE IF EXISTS confluence_pages CASCADE;
DROP TABLE IF EXISTS employees CASCADE;

-- Recreate by running 000_complete_schema.sql
```

---

## Running the Application

### Start Development Server

```bash
python manage.py runserver
```

Server runs at: http://127.0.0.1:8000/

### Access Admin Panel

http://127.0.0.1:8000/admin/

### Create Superuser (First Time)

```bash
python manage.py createsuperuser
```

---

## Data Ingestion

The `ingest_data` command imports data from local files (CSV, JSON, VTT, MD).

### Available Options

| Option | File Type | Description |
|--------|-----------|-------------|
| `--employees` | CSV | Import employee data |
| `--projects` | CSV | Import project data |
| `--jira` | CSV | Import Jira tickets |
| `--sprints` | CSV | Import sprint data |
| `--sprint-tickets` | CSV | Import sprint-ticket links |
| `--commits` | JSON | Import git commits |
| `--meetings` | VTT | Import meeting transcript |
| `--confluence` | MD | Import Confluence page |

### Ingestion Order (Important!)

Run in this order due to foreign key dependencies:

```bash
cd ~/Desktop/Onboarding_AI/database
source ../venv/bin/activate

# 1. Employees (no dependencies)
python manage.py ingest_data --employees /path/to/employees.csv

# 2. Projects (no dependencies)
python manage.py ingest_data --projects /path/to/projects.csv

# 3. Jira tickets (no dependencies)
python manage.py ingest_data --jira /path/to/jira_tickets.csv

# 4. Sprints (requires projects)
python manage.py ingest_data --sprints /path/to/sprints.csv

# 5. Sprint-tickets (requires sprints + tickets)
python manage.py ingest_data --sprint-tickets /path/to/sprint_tickets.csv

# 6. Git commits (no dependencies)
python manage.py ingest_data --commits /path/to/git_commits.json

# 7. Meetings (run for each VTT file)
python manage.py ingest_data --meetings /path/to/meeting1.vtt
python manage.py ingest_data --meetings /path/to/meeting2.vtt

# 8. Confluence pages (run for each MD file)
python manage.py ingest_data --confluence /path/to/page1.md
python manage.py ingest_data --confluence /path/to/page2.md
```

### Example: Ingest All Synthetic Data

```bash
# Set base path
DATA_PATH=/path/to/synthetic_data

# Ingest in order
python manage.py ingest_data --employees $DATA_PATH/employees.csv
python manage.py ingest_data --projects $DATA_PATH/projects.csv
python manage.py ingest_data --jira $DATA_PATH/jira_tickets.csv
python manage.py ingest_data --sprints $DATA_PATH/sprints.csv
python manage.py ingest_data --sprint-tickets $DATA_PATH/sprint_tickets.csv
python manage.py ingest_data --commits $DATA_PATH/git_commits.json

# Meetings
for f in $DATA_PATH/vtt/*.vtt; do
    python manage.py ingest_data --meetings "$f"
done

# Confluence pages
for f in $DATA_PATH/confluence/*.md; do
    python manage.py ingest_data --confluence "$f"
done
```

### File Formats

#### employees.csv
```csv
name,email,role,department,source,github_username,is_active
Sarah Chen,sarah.chen@company.com,Tech Lead,Engineering,csv,sarahchen,true
```

#### projects.csv
```csv
name,description,status,epic_key,jira_project_key,github_repo,confluence_space_key,start_date,target_end_date,owner,team_members,tags
My Project,Description here,active,ONBOARD-10,ONBOARD,org/repo,Space Key,2026-01-06,2026-02-14,Sarah Chen,"[""Member1""]","[""tag1""]"
```

#### sprints.csv
```csv
sprint_number,name,start_date,end_date,goal,project_name,status
1,Sprint 1 - Foundation,2026-01-06,2026-01-17,Build foundation,Employee Onboarding Portal,completed
```

#### sprint_tickets.csv
```csv
sprint_number,ticket_key,added_date
1,ONBOARD-11,2026-01-06
```

#### jira_tickets.csv
```csv
Issue Key,Issue Type,Summary,Description,Status,Priority,Assignee,Reporter,Created,Updated,Resolved,Labels,Epic Link,Sprint,Story Points,Comments
ONBOARD-11,Task,Initialize project,Setup Django,Done,High,Marcus,Sarah,2026-01-06,2026-01-06,2026-01-06,backend,ONBOARD-10,Sprint 1,2,"[comment text]"
```

#### git_commits.json
```json
[
  {
    "sha": "abc123...",
    "commit": {
      "author": {
        "name": "Marcus Thompson",
        "email": "marcus@company.com",
        "date": "2026-01-06T09:30:00Z"
      },
      "message": "feat: add feature\n\nRelated: ONBOARD-11"
    },
    "files": [
      {"filename": "file.py", "additions": 50, "deletions": 10, "status": "modified"}
    ]
  }
]
```

#### meetings (VTT format)
```
WEBVTT

NOTE
Meeting: Sprint Planning
Date: 2026-01-06
Participants: Sarah Chen (Tech Lead), Marcus Thompson (Dev)

00:00:05.000 --> 00:00:12.000
Sarah Chen: Welcome everyone to sprint planning.
```

#### confluence pages (Markdown with frontmatter)
```markdown
title: "Page Title"
space: "Onboarding Portal"
author: "Sarah Chen"
created: "2026-01-06"
last_updated: "2026-01-20"
labels: ["guide", "setup"]
version: 3

# Page Title

Content here...
```

---

## Data Extraction Scripts

Extract data directly from APIs (GitHub, Jira, Confluence).

| Script | Source | Command |
|--------|--------|---------|
| `extract_github.py` | GitHub API | `python scripts/extract_github.py` |
| `extract_confluence.py` | Confluence API | `python scripts/extract_confluence.py` |
| `extract_jira.py` | Jira API | `python scripts/extract_jira.py` |

### Run All Extractions

```bash
python scripts/extract_github.py
python scripts/extract_confluence.py
python scripts/extract_jira.py
```

Scripts automatically:
- Create/update records (no duplicates)
- Extract ticket references from content
- Create `entity_references` links

---

## Working with the Database

### Useful SQL Queries

```sql
-- Count all records
SELECT 'employees' as tbl, COUNT(*) FROM employees
UNION ALL SELECT 'commits', COUNT(*) FROM git_commits
UNION ALL SELECT 'tickets', COUNT(*) FROM jira_tickets
UNION ALL SELECT 'pages', COUNT(*) FROM confluence_pages
UNION ALL SELECT 'meetings', COUNT(*) FROM meetings
UNION ALL SELECT 'sprints', COUNT(*) FROM sprints
UNION ALL SELECT 'references', COUNT(*) FROM entity_references;

-- View sprint with tickets
SELECT s.name, s.start_date, s.end_date, j.issue_key, j.summary
FROM sprints s
JOIN sprint_tickets st ON s.id = st.sprint_id
JOIN jira_tickets j ON st.ticket_id = j.id
ORDER BY s.sprint_number, j.issue_key;

-- Find everything related to a ticket
SELECT source_type, reference_id, extraction_method
FROM entity_references
WHERE reference_id = 'ONBOARD-11';

-- View project timeline
SELECT * FROM unified_timeline
ORDER BY event_date DESC
LIMIT 20;
```

### Django Shell

```bash
python manage.py shell
```

```python
from knowledge_base.models import *

# Count records
print(f"Employees: {Employee.objects.count()}")
print(f"Commits: {GitCommit.objects.count()}")
print(f"Tickets: {JiraTicket.objects.count()}")
print(f"Sprints: {Sprint.objects.count()}")

# Get sprint with tickets
sprint = Sprint.objects.get(sprint_number=1)
for st in sprint.sprint_tickets.all():
    print(f"  {st.ticket.issue_key}: {st.ticket.summary}")

# Find commits for a ticket
refs = EntityReference.objects.filter(
    reference_type='jira_ticket',
    reference_id='ONBOARD-11',
    source_type='commit'
)
for ref in refs:
    commit = GitCommit.objects.get(id=ref.source_id)
    print(f"{commit.sha[:7]}: {commit.message[:50]}")
```

---

## Django Admin

### Available Models in Admin

| Model | Description |
|-------|-------------|
| **Employees** | View/edit team members |
| **Git Commits** | View commits with search |
| **Git Commit Files** | Files changed per commit |
| **Jira Tickets** | Filter by status, assignee |
| **Confluence Pages** | View documentation |
| **Meetings** | Meeting transcripts |
| **Entity References** | Cross-links |
| **Projects** | Project groupings |
| **Project Entities** | Entity links |
| **Sprints** | Sprint data |
| **Sprint Tickets** | Sprint-ticket links |

---

## API Credentials

### Where to Get Tokens

| Service | URL |
|---------|-----|
| GitHub PAT | https://github.com/settings/tokens |
| Atlassian API Token | https://id.atlassian.com/manage-profile/security/api-tokens |

### Test API Connections

```bash
# GitHub
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Jira
curl -u your-email:YOUR_TOKEN "https://your-domain.atlassian.net/rest/api/3/myself"

# Confluence
curl -u your-email:YOUR_TOKEN "https://your-domain.atlassian.net/wiki/api/v2/spaces"
```

---

## Common Tasks

### Add New Employee

```bash
python manage.py ingest_data --employees /path/to/new_employee.csv
```

Or via Django shell:
```python
from knowledge_base.models import Employee
Employee.objects.create(
    name="James O'Brien",
    email="james@company.com",
    role="Junior Developer",
    department="Engineering",
    is_active=True
)
```

### Add New Sprint

```bash
python manage.py ingest_data --sprints /path/to/new_sprint.csv
python manage.py ingest_data --sprint-tickets /path/to/sprint_tickets.csv
```

### Export Data

```bash
python manage.py dumpdata knowledge_base --indent 2 > data_export.json
```

---

## Troubleshooting

### "Module not found" errors

```bash
source ../venv/bin/activate
pip install -r requirements.txt
```

### "Connection refused" to database

Check your `.env` has the correct Render database URL.

### "Sprint not found" when ingesting sprint-tickets

Make sure you ingest sprints BEFORE sprint-tickets.

### "Project not found" when ingesting sprints

Make sure you ingest projects BEFORE sprints.

### Scripts run but no data appears

1. Check `.env` file has correct values
2. Check for error messages in output
3. Verify database connection

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Activate venv | `source ../venv/bin/activate` |
| Start server | `python manage.py runserver` |
| Django shell | `python manage.py shell` |
| Check setup | `python manage.py check` |
| Create superuser | `python manage.py createsuperuser` |
| Ingest employees | `python manage.py ingest_data --employees FILE` |
| Ingest projects | `python manage.py ingest_data --projects FILE` |
| Ingest jira | `python manage.py ingest_data --jira FILE` |
| Ingest sprints | `python manage.py ingest_data --sprints FILE` |
| Ingest sprint-tickets | `python manage.py ingest_data --sprint-tickets FILE` |
| Ingest commits | `python manage.py ingest_data --commits FILE` |
| Ingest meeting | `python manage.py ingest_data --meetings FILE` |
| Ingest confluence | `python manage.py ingest_data --confluence FILE` |
| Connect to DB | `psql "postgresql://..."` |

---

## Need Help?

1. Check `DATABASE.md` for schema details
2. Check `DB_CONNECTION_GUIDE.md` for connection info
3. Check `EMPLOYEES_TABLE.md` for employee queries
4. Check Django logs in terminal for errors

---

*Last updated: February 2026*