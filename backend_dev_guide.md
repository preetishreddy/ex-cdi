# Onboarding AI - Backend Developer Guide

A practical guide for backend developers working on the Onboarding AI project.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Environment Setup](#environment-setup)
4. [Running the Application](#running-the-application)
5. [Data Extraction Scripts](#data-extraction-scripts)
6. [Working with the Database](#working-with-the-database)
7. [Django Admin](#django-admin)
8. [API Credentials](#api-credentials)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting](#troubleshooting)

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
    │   ├── models.py             # Database models (8 models)
    │   ├── admin.py              # Admin interface configuration
    │   └── management/
    │       └── commands/
    │           └── ingest_data.py    # Legacy file ingestion
    │
    ├── scripts/                  # Data extraction scripts
    │   ├── extract_github.py     # Fetch commits from GitHub
    │   ├── extract_confluence.py # Fetch pages from Confluence
    │   └── extract_jira.py       # Fetch tickets from Jira
    │
    ├── sql/
    │   └── 001_create_schema.sql # Original SQL schema
    │
    └── docs/
        ├── BACKEND_DEVELOPER_GUIDE.md
        └── DATA_SOURCE_SETUP_GUIDE.md
```

---

## Environment Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (we use PostgreSQL 18)
- Git

### Step 1: Clone and Navigate

```bash
cd ~/Desktop/Onboarding_AI/database
```

### Step 2: Create Virtual Environment (if not exists)

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
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required variables:**

```bash
# Database
DB_NAME=project_knowledge
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
DEBUG=True
SECRET_KEY=your-secret-key-here

# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_OWNER=nkousik18
GITHUB_REPO=LoanQA-MLOps

# Jira & Confluence (same token works for both)
JIRA_DOMAIN=onboardingaii.atlassian.net
JIRA_EMAIL=your-email@gmail.com
JIRA_API_TOKEN=your-atlassian-api-token
JIRA_PROJECT_KEY=ONBOARD

CONFLUENCE_DOMAIN=onboardingaii.atlassian.net
CONFLUENCE_EMAIL=your-email@gmail.com
CONFLUENCE_API_TOKEN=your-atlassian-api-token
CONFLUENCE_SPACE_KEY=ONBOARD
CONFLUENCE_SPACE_ID=1474564
```

### Step 5: Verify Database Connection

```bash
python manage.py check
```

If successful, you'll see: `System check identified no issues (0 silenced).`

### Step 6: Run Migrations (first time only)

```bash
python manage.py migrate
```

This creates Django's internal tables (auth, sessions, etc.).

---

## Running the Application

### Start Development Server

```bash
python manage.py runserver
```

Server runs at: http://127.0.0.1:8000/

### Start on Different Port

```bash
python manage.py runserver 8080
```

### Run in Background (optional)

```bash
python manage.py runserver &
```

---

## Data Extraction Scripts

### Overview

| Script | Source | What It Extracts |
|--------|--------|------------------|
| `extract_github.py` | GitHub API | Commits + files changed |
| `extract_confluence.py` | Confluence API | Pages + content (as Markdown) |
| `extract_jira.py` | Jira API | Tickets + comments |

All scripts automatically create `entity_references` to link data.

---

### Running GitHub Extraction

**Extracts:** Commits and files changed from a repository.

```bash
# Activate environment first
source ../venv/bin/activate

# Run extraction
python scripts/extract_github.py
```

**Environment variables used:**
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_OWNER=nkousik18          # Repository owner
GITHUB_REPO=LoanQA-MLOps        # Repository name
GITHUB_MAX_COMMITS=100          # Max commits to fetch
```

**What happens:**
1. Fetches commit list from GitHub API
2. For each commit, fetches file changes
3. Saves to `git_commits` and `git_commit_files` tables
4. Scans commit messages for ticket references (e.g., `ONBOARD-5`)
5. Creates `entity_references` links

**Output:**
```
============================================================
Extracting commits from nkousik18/LoanQA-MLOps
============================================================

Fetching commits page 1...
  Found 25 commits

[1/25] Processing a1b2c3d...
  ✓ Created: Initial commit
[2/25] Processing d4e5f6g...
  ✓ Created: Add authentication module

============================================================
Extraction Complete!
============================================================
  Created: 25
  Updated: 0
  Errors:  0
  Total:   25
```

---

### Running Confluence Extraction

**Extracts:** Pages from a Confluence space (converted to Markdown).

```bash
python scripts/extract_confluence.py
```

**Environment variables used:**
```bash
CONFLUENCE_DOMAIN=onboardingaii.atlassian.net
CONFLUENCE_EMAIL=your-email@gmail.com
CONFLUENCE_API_TOKEN=your-token
CONFLUENCE_SPACE_KEY=ONBOARD
CONFLUENCE_SPACE_ID=1474564
```

**What happens:**
1. Fetches page list from Confluence API
2. For each page, fetches full content
3. Converts HTML/XML to readable Markdown
4. Saves to `confluence_pages` table
5. Scans content for ticket references
6. Creates `entity_references` links

**Output:**
```
============================================================
Extracting pages from space: ONBOARD (ID: 1474564)
============================================================

Fetching pages...
  Found 8 pages

Total pages to process: 8

[1/8] Processing: Onboarding AI
  ✓ Created: Onboarding AI
[2/8] Processing: Database Schema
  ✓ Created: Database Schema
[3/8] Processing: Template - How-to guide
  ⊘ Skipping template page

============================================================
Extraction Complete!
============================================================
  Created: 6
  Updated: 0
  Errors:  0
  Total:   8
```

---

### Running Jira Extraction

**Extracts:** Tickets from a Jira project.

```bash
python scripts/extract_jira.py
```

**Environment variables used:**
```bash
JIRA_DOMAIN=onboardingaii.atlassian.net
JIRA_EMAIL=your-email@gmail.com
JIRA_API_TOKEN=your-token
JIRA_PROJECT_KEY=ONBOARD
JIRA_MAX_ISSUES=500
```

**What happens:**
1. Searches for issues using JQL: `project = ONBOARD`
2. For each issue, fetches comments
3. Saves to `jira_tickets` table
4. Creates `entity_references` for epic links

**Output:**
```
============================================================
Extracting issues from project: ONBOARD
============================================================

Fetching issues...
  Found 10 issues (total: 10)

Total issues to process: 10

[1/10] Processing: ONBOARD-1 - Data Extraction Pipeline...
  ✓ Created
[2/10] Processing: ONBOARD-2 - Implement GitHub extraction...
  ✓ Created

============================================================
Extraction Complete!
============================================================
  Created: 10
  Updated: 0
  Errors:  0
  Total:   10
```

---

### Running All Extractions

Create a simple script to run all:

```bash
#!/bin/bash
# run_all_extractions.sh

echo "Starting data extraction..."

echo "\n>>> Extracting GitHub commits..."
python scripts/extract_github.py

echo "\n>>> Extracting Confluence pages..."
python scripts/extract_confluence.py

echo "\n>>> Extracting Jira tickets..."
python scripts/extract_jira.py

echo "\n>>> All extractions complete!"
```

Run it:
```bash
chmod +x run_all_extractions.sh
./run_all_extractions.sh
```

---

### Re-running Extractions

**Safe to re-run!** Scripts use `update_or_create`:
- New records → Created
- Existing records → Updated
- No duplicates created

---

## Working with the Database

### Connect to PostgreSQL

```bash
/Library/PostgreSQL/18/bin/psql -U postgres -d project_knowledge
```

### Useful SQL Commands

```sql
-- List all tables
\dt

-- Describe a table
\d git_commits

-- Count records
SELECT COUNT(*) FROM git_commits;
SELECT COUNT(*) FROM jira_tickets;
SELECT COUNT(*) FROM confluence_pages;
SELECT COUNT(*) FROM entity_references;

-- View recent commits
SELECT sha, author_name, commit_date, LEFT(message, 50) 
FROM git_commits 
ORDER BY commit_date DESC 
LIMIT 10;

-- Find all references to a ticket
SELECT * FROM entity_references 
WHERE reference_id = 'ONBOARD-5';

-- View timeline
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
GitCommit.objects.count()
JiraTicket.objects.count()
ConfluencePage.objects.count()

# Get all commits
commits = GitCommit.objects.all()

# Filter tickets by status
open_tickets = JiraTicket.objects.filter(status='To Do')

# Find commits referencing a ticket
refs = EntityReference.objects.filter(
    reference_type='jira_ticket',
    reference_id='ONBOARD-5',
    source_type='commit'
)
commit_ids = refs.values_list('source_id', flat=True)
commits = GitCommit.objects.filter(id__in=commit_ids)

# Get files for a commit
commit = GitCommit.objects.first()
files = commit.files.all()
for f in files:
    print(f"{f.filename}: +{f.additions} -{f.deletions}")
```

---

## Django Admin

### Access Admin Panel

1. Start server: `python manage.py runserver`
2. Go to: http://127.0.0.1:8000/admin/
3. Login with superuser credentials

### Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

### Available in Admin

- **Git Commits** - View/search commits
- **Git Commit Files** - View files changed
- **Meetings** - View meeting transcripts
- **Jira Tickets** - View/filter tickets
- **Confluence Pages** - View documentation
- **Entity References** - View cross-references
- **Projects** - Manage project groupings
- **Project Entities** - View entity links

### Reset Admin Password

```bash
python manage.py changepassword your_username
```

---

## API Credentials

### Where to Get Tokens

| Service | URL |
|---------|-----|
| GitHub PAT | https://github.com/settings/tokens |
| Atlassian API Token | https://id.atlassian.com/manage-profile/security/api-tokens |

### GitHub Token Scopes Needed

- `repo` - Full control of private repositories
- `read:org` - Read organization info (if using org repos)

### Atlassian Token

Same token works for both Jira and Confluence.

### Testing API Connections

**GitHub:**
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/user
```

**Jira:**
```bash
curl -u your-email:YOUR_TOKEN \
  "https://onboardingaii.atlassian.net/rest/api/3/myself"
```

**Confluence:**
```bash
curl -u your-email:YOUR_TOKEN \
  "https://onboardingaii.atlassian.net/wiki/api/v2/spaces"
```

---

## Common Tasks

### Add a New Data Source

1. Create extraction script in `scripts/`
2. Follow the pattern of existing scripts:
   - Load environment variables
   - Set up Django
   - Define API functions
   - Save to database
   - Extract entity references

### Modify Database Schema

1. Add SQL to a new migration file in `sql/`
2. Run SQL manually in PostgreSQL
3. Update Django model in `knowledge_base/models.py`
4. Update admin in `knowledge_base/admin.py`

### Add New Entity Reference Pattern

Edit the `extract_jira_references()` function in scripts:

```python
def extract_jira_references(text):
    if not text:
        return []
    # Add more patterns here
    pattern = r'[A-Z]+-\d+'  # Matches ONBOARD-5, PROJ-123, etc.
    matches = re.findall(pattern, text)
    return list(set(matches))
```

### Export Data

```bash
# Export to JSON
python manage.py dumpdata knowledge_base --indent 2 > data_export.json

# Export specific model
python manage.py dumpdata knowledge_base.gitcommit --indent 2 > commits.json
```

### Import Data

```bash
python manage.py loaddata data_export.json
```

---

## Troubleshooting

### "Module not found" errors

```bash
# Make sure venv is activated
source ../venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Connection refused" to database

```bash
# Check if PostgreSQL is running
# On Mac, check Applications > PostgreSQL 18

# Test connection
/Library/PostgreSQL/18/bin/psql -U postgres -d project_knowledge
```

### "Authentication failed" for APIs

1. Check token hasn't expired
2. Verify email address is correct
3. Regenerate token if needed

### "No module named 'knowledge_base'"

Make sure you're in the right directory:
```bash
cd ~/Desktop/Onboarding_AI/database
```

### Scripts run but no data appears

1. Check `.env` file has correct values
2. Check API tokens are valid
3. Check project keys match (ONBOARD vs PAY, etc.)
4. Look for error messages in script output

### Clear all data and start fresh

```sql
-- Connect to PostgreSQL
TRUNCATE git_commits CASCADE;
TRUNCATE jira_tickets CASCADE;
TRUNCATE confluence_pages CASCADE;
TRUNCATE meetings CASCADE;
TRUNCATE entity_references CASCADE;
TRUNCATE projects CASCADE;
TRUNCATE project_entities CASCADE;
```

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Activate venv | `source ../venv/bin/activate` |
| Start server | `python manage.py runserver` |
| Run GitHub extraction | `python scripts/extract_github.py` |
| Run Confluence extraction | `python scripts/extract_confluence.py` |
| Run Jira extraction | `python scripts/extract_jira.py` |
| Django shell | `python manage.py shell` |
| Check setup | `python manage.py check` |
| Create superuser | `python manage.py createsuperuser` |
| Connect to DB | `/Library/PostgreSQL/18/bin/psql -U postgres -d project_knowledge` |

---

## Need Help?

1. Check `DATABASE.md` for schema details
2. Check `docs/DATA_SOURCE_SETUP_GUIDE.md` for API setup
3. Check Django logs in terminal for errors
4. Use Django shell to debug queries

---

*Last updated: February 2026*