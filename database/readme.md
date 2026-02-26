# Onboarding_AI - Database Module

Django application for the knowledge base database, storing and linking project knowledge from:
- Git Commits
- Meeting Transcripts (VTT)
- Jira Tickets
- Confluence Pages

## Project Structure

```
Onboarding_AI/
└── database/
    ├── manage.py                 # Django CLI
    ├── requirements.txt          # Python dependencies
    ├── .env.example             # Environment template
    ├── .gitignore
    ├── sql/
    │   └── 001_create_schema.sql # PostgreSQL schema (already applied)
    ├── config/                   # Django project settings
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── knowledge_base/           # Main Django app
        ├── __init__.py
        ├── apps.py
        ├── models.py             # Database models
        ├── admin.py              # Admin interface
        └── management/
            └── commands/
                └── ingest_data.py    # Data ingestion command
```

## Quick Setup

### Step 1: Navigate to the database folder

```bash
cd Onboarding_AI/database
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate   # On macOS/Linux
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:
```
DB_NAME=project_knowledge
DB_USER=postgres
DB_PASSWORD=your_actual_password
DB_HOST=localhost
DB_PORT=5432
DEBUG=True
SECRET_KEY=some-random-secret-key
```

### Step 5: Verify Database Connection

```bash
python manage.py check
```

### Step 6: Run Django Migrations

This creates Django's internal tables (admin, sessions, etc.):

```bash
python manage.py migrate
```

### Step 7: Create Admin User

```bash
python manage.py createsuperuser
```

### Step 8: Start Development Server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/admin/ to access the admin interface.

---

## Ingesting Data

### Git Commits (JSON)

```bash
python manage.py ingest_data --commits /path/to/commits.json
```

### Meeting Transcripts (VTT)

```bash
python manage.py ingest_data --meetings /path/to/meeting.vtt
```

### Jira Tickets (CSV)

```bash
python manage.py ingest_data --jira /path/to/tickets.csv
```

### Confluence Pages (Markdown)

```bash
python manage.py ingest_data --confluence /path/to/page.md
```

---

## Example Queries (Django Shell)

```bash
python manage.py shell
```

```python
from knowledge_base.models import *

# Get all commits by an author
dave_commits = GitCommit.objects.filter(author_name='Dave Rossi')

# Get all open tickets
open_tickets = JiraTicket.objects.filter(status='In Progress')

# Find everything related to a ticket
refs = EntityReference.objects.filter(
    reference_type='jira_ticket',
    reference_id='PAY-204'
)

# Get commits that reference a ticket
commit_ids = refs.filter(source_type='commit').values_list('source_id', flat=True)
related_commits = GitCommit.objects.filter(id__in=commit_ids)
```

---

## Database Tables

| Table | Description |
|-------|-------------|
| `git_commits` | Git commit metadata |
| `git_commit_files` | Files changed per commit |
| `meetings` | Meeting transcripts and summaries |
| `jira_tickets` | Jira issues |
| `confluence_pages` | Documentation pages |
| `entity_references` | Links between all entities |

---

## Troubleshooting

### "password authentication failed"
Check your `.env` file has the correct password.

### "relation does not exist"
The database tables weren't created. Connect to PostgreSQL and run:
```bash
/Library/PostgreSQL/18/bin/psql -U postgres -d project_knowledge -f sql/001_create_schema.sql
```

### Can't connect to PostgreSQL
Make sure PostgreSQL 18 is running. Check Applications → PostgreSQL 18.