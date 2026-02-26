# Onboarding AI - Database Connection Guide

A guide for developers to connect to and use the Onboarding AI database.

---

## Connection Details

| Field | Value |
|-------|-------|
| **Host** | `dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com` |
| **Port** | `5432` |
| **Database** | `project_knowledge` |
| **Username** | `onboarding_user` |
| **Password** | `T9hSACQXUiLLlJfNcxM1hBEwwRWYAnvQ` |

**Full Connection String:**
```
postgresql://onboarding_user:T9hSACQXUiLLlJfNcxM1hBEwwRWYAnvQ@dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com/project_knowledge
```

---

## Connection Methods

### Method 1: Command Line (psql)

```bash
psql "postgresql://onboarding_user:T9hSACQXUiLLlJfNcxM1hBEwwRWYAnvQ@dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com/project_knowledge"
```

If connected successfully, you'll see:
```
project_knowledge=>
```

### Method 2: GUI Tools (Recommended)

#### DBeaver (Free, Cross-platform)
1. Download from: https://dbeaver.io/download/
2. Click **Database** → **New Database Connection**
3. Select **PostgreSQL**
4. Enter connection details:
   - Host: `dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com`
   - Port: `5432`
   - Database: `project_knowledge`
   - Username: `onboarding_user`
   - Password: `T9hSACQXUiLLlJfNcxM1hBEwwRWYAnvQ`
5. Click **Test Connection** → **Finish**

#### TablePlus (Mac/Windows, Free Tier)
1. Download from: https://tableplus.com/
2. Click **+** to create new connection
3. Select **PostgreSQL**
4. Enter connection details (same as above)
5. Click **Connect**

#### pgAdmin (Free, Cross-platform)
1. Download from: https://www.pgadmin.org/download/
2. Right-click **Servers** → **Register** → **Server**
3. Name: `Onboarding AI`
4. Connection tab: Enter details (same as above)
5. Click **Save**

### Method 3: Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host="dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com",
    port="5432",
    database="project_knowledge",
    user="onboarding_user",
    password="T9hSACQXUiLLlJfNcxM1hBEwwRWYAnvQ"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM git_commits;")
print(cursor.fetchone())

conn.close()
```

### Method 4: Django Shell

```bash
cd ~/Desktop/Onboarding_AI/database
source ../venv/bin/activate
python manage.py shell
```

```python
from knowledge_base.models import *

# Query data
commits = GitCommit.objects.all()
tickets = JiraTicket.objects.all()
pages = ConfluencePage.objects.all()
```

---

## Database Schema Overview

### Tables

| Table | Description | Key Fields |
|-------|-------------|------------|
| `git_commits` | Git commit metadata | sha, author_name, message, commit_date |
| `git_commit_files` | Files changed per commit | commit_id, filename, additions, deletions |
| `jira_tickets` | Jira issues | issue_key, summary, status, assignee |
| `confluence_pages` | Confluence documentation | title, content, space, author |
| `meetings` | Meeting transcripts | title, raw_vtt_content, participants |
| `entity_references` | Cross-links between entities | source_type, source_id, reference_id |
| `projects` | Project groupings | name, github_repo, jira_project_key |
| `project_entities` | Links entities to projects | project_id, entity_type, entity_id |

### Key Relationships

```
git_commits (1) ──────> (N) git_commit_files
     │
     │
     ▼
entity_references  <──── jira_tickets
     ▲                        
     │                        
     └─────────────────  confluence_pages, meetings
```

---

## Common Queries

### View All Tables
```sql
\dt
```

### Count Records in All Tables
```sql
SELECT 'git_commits' as table_name, COUNT(*) as count FROM git_commits
UNION ALL SELECT 'git_commit_files', COUNT(*) FROM git_commit_files
UNION ALL SELECT 'jira_tickets', COUNT(*) FROM jira_tickets
UNION ALL SELECT 'confluence_pages', COUNT(*) FROM confluence_pages
UNION ALL SELECT 'meetings', COUNT(*) FROM meetings
UNION ALL SELECT 'entity_references', COUNT(*) FROM entity_references
UNION ALL SELECT 'projects', COUNT(*) FROM projects;
```

### View Recent Commits
```sql
SELECT sha, author_name, commit_date, LEFT(message, 60) as message
FROM git_commits
ORDER BY commit_date DESC
LIMIT 10;
```

### View Jira Tickets by Status
```sql
SELECT issue_key, summary, status, assignee
FROM jira_tickets
ORDER BY created_date DESC;
```

### View Confluence Pages
```sql
SELECT title, author, space, page_updated_date
FROM confluence_pages
ORDER BY page_updated_date DESC;
```

### Find Everything Related to a Ticket
```sql
-- Get all references to a specific ticket
SELECT source_type, source_id, extraction_method
FROM entity_references
WHERE reference_type = 'jira_ticket'
AND reference_id = 'ONBOARD-1';
```

### Get Commits for a Ticket
```sql
SELECT c.sha, c.author_name, c.message, c.commit_date
FROM git_commits c
JOIN entity_references er ON c.id = er.source_id
WHERE er.source_type = 'commit'
AND er.reference_type = 'jira_ticket'
AND er.reference_id = 'ONBOARD-1';
```

### View Project Timeline
```sql
SELECT * FROM unified_timeline
ORDER BY event_date DESC
LIMIT 20;
```

### Search Confluence by Label
```sql
SELECT title, author, labels
FROM confluence_pages
WHERE 'database' = ANY(labels);
```

---

## Django ORM Examples

```python
from knowledge_base.models import *

# Get all commits by an author
commits = GitCommit.objects.filter(author_name__icontains='kousik')

# Get open tickets
open_tickets = JiraTicket.objects.exclude(status='Done')

# Get files changed in a commit
commit = GitCommit.objects.first()
files = commit.files.all()

# Find everything linked to a ticket
refs = EntityReference.objects.filter(
    reference_type='jira_ticket',
    reference_id='ONBOARD-1'
)

# Get commits linked to a ticket
commit_ids = refs.filter(source_type='commit').values_list('source_id', flat=True)
related_commits = GitCommit.objects.filter(id__in=commit_ids)

# Search Confluence pages
pages = ConfluencePage.objects.filter(content__icontains='database')
```

---

## Useful psql Commands

| Command | Description |
|---------|-------------|
| `\dt` | List all tables |
| `\d table_name` | Describe table structure |
| `\dv` | List all views |
| `\l` | List all databases |
| `\q` | Quit psql |
| `\x` | Toggle expanded display |

---

## Troubleshooting

### "Connection refused"
- Check if you have internet connection
- Verify the hostname is correct
- Render free tier databases sleep after 15 min of inactivity - just wait a moment

### "Password authentication failed"
- Double-check username and password
- Ensure no extra spaces when copying

### "SSL required"
Some clients need SSL. Add `?sslmode=require` to connection string:
```
postgresql://onboarding_user:T9hSACQXUiLLlJfNcxM1hBEwwRWYAnvQ@dpg-d6evhe8gjchc73ac2mmg-a.oregon-postgres.render.com/project_knowledge?sslmode=require
```

---

## Security Notes

⚠️ **Important:**
- Do not commit credentials to Git
- Use environment variables in production
- Rotate passwords periodically
- The free tier database is publicly accessible - do not store sensitive data

---

## Need Help?

- Check `DATABASE.md` for full schema documentation
- Check `DEVELOPER_GUIDE.md` for setup instructions
- Contact the project owner for access issues

---

*Last updated: February 2026*