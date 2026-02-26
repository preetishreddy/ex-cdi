# Onboarding AI — Progress Checkpoint

_Last updated: February 25, 2026_

---

## Project Overview

**Onboarding AI** is a tool that ingests engineering data (GitHub commits, Jira tickets,
Confluence pages, meeting transcripts) into a PostgreSQL database and exposes it via a
REST API so an AI/frontend layer can answer onboarding questions.

**Stack:** Python 3.11 · Django 5.2 · Django REST Framework 3.16 · PostgreSQL (Render)

---

## Milestone 1 — Django Project + Database Setup ✅

_Commit: `42d9824` — "Initial commit: django and db setup"_

### What was built
- Root Django project (`config/`) pointing at a Render-hosted PostgreSQL database
- `knowledge_base` app with 8 unmanaged models that map to the pre-existing schema:

| Model | DB Table | Description |
|---|---|---|
| `GitCommit` | `git_commits` | Commit SHA, author, date, message |
| `GitCommitFile` | `git_commit_files` | Files changed per commit |
| `JiraTicket` | `jira_tickets` | Tickets with status, priority, comments |
| `ConfluencePage` | `confluence_pages` | Pages with full Markdown content |
| `Meeting` | `meetings` | Transcripts, summaries, action items |
| `EntityReference` | `entity_references` | Cross-source links (e.g. commit → ticket) |
| `Project` | `projects` | Groups of related entities |
| `ProjectEntity` | `project_entities` | Many-to-many: project ↔ entity |

- Data extraction scripts in `database/scripts/`:
  - `extract_github.py` — fetches commits + file diffs from GitHub API
  - `extract_jira.py` — fetches tickets + comments from Jira API
  - `extract_confluence.py` — fetches pages (HTML → Markdown) from Confluence API
- Database fully populated with real data on Render

---

## Milestone 2 — REST API Endpoints ✅

_This session — February 25, 2026_

### What was built

Added **Django REST Framework** and implemented 12 endpoints across 5 resources.

#### Files changed

| File | Change |
|---|---|
| `requirements.txt` | Added `djangorestframework==3.16.0` |
| `config/settings.py` | Added `'rest_framework'` to `INSTALLED_APPS` |
| `api/serializers.py` | **Created** — 8 `ModelSerializer` classes |
| `api/views.py` | **Replaced** health stub with 12 DRF view classes |
| `api/urls.py` | **Replaced** with 13 URL patterns |

#### Endpoint reference

| Method | URL | Description |
|---|---|---|
| GET | `/api/commits/` | All commits, ordered by date (with nested files) |
| GET | `/api/commits/<sha>/` | Single commit + all changed files |
| GET | `/api/tickets/` | All Jira tickets |
| GET | `/api/tickets/<issue_key>/` | Single ticket |
| GET | `/api/tickets/<issue_key>/context/` | Ticket + linked commits, pages, meetings via `entity_references` |
| GET | `/api/pages/` | All Confluence pages (no content body) |
| GET | `/api/pages/<id>/` | Single page with full content |
| GET | `/api/meetings/` | All meetings (no transcript) |
| GET | `/api/meetings/<id>/` | Single meeting with full transcript |
| GET | `/api/projects/` | All projects + linked entity list |
| GET | `/api/projects/<id>/` | Single project + linked entity list |
| GET | `/api/search/?q=<query>` | Full-text search across commits, tickets, pages, meetings |

#### Serializer design decisions
- `ConfluencePageListSerializer` — omits `content` on list to avoid large payloads
- `MeetingListSerializer` — omits `raw_vtt_content` on list
- `GitCommitSerializer` — nests `GitCommitFileSerializer` (files always included)
- `ProjectSerializer` — nests `ProjectEntitySerializer` (entity list always included)

#### Verified live
```
curl http://127.0.0.1:8000/api/commits/
# → returns real commit records from Render DB ✓
```

---

## Current Project Structure

```
ex-cdi/
├── manage.py
├── requirements.txt          ← Django 5.2, DRF 3.16, psycopg2-binary
├── .env                      ← DB credentials (not committed)
├── .env.example
├── PROGRESS.md               ← this file
├── README.md
├── backend_dev_guide.md
│
├── config/
│   ├── settings.py           ← INSTALLED_APPS includes rest_framework
│   ├── urls.py               ← /api/ → api.urls, /admin/ → admin
│   └── wsgi.py
│
├── knowledge_base/
│   ├── models.py             ← 8 unmanaged models
│   └── admin.py
│
└── api/
    ├── serializers.py        ← 8 ModelSerializers
    ├── views.py              ← 12 view classes
    └── urls.py               ← 13 URL patterns
```

---

## What's Next

### Milestone 3 — Authentication
- Add token-based auth (JWT via `djangorestframework-simplejwt`)
- Protect all `/api/` routes behind `IsAuthenticated`
- Create user model or hook into Django's built-in auth

### Milestone 4 — AI / LLM Layer
- Design a `/api/ask/` endpoint that accepts a natural-language question
- Use search + entity context endpoints to build a retrieval payload
- Send payload to Claude or OpenAI and stream the answer back

### Milestone 5 — Frontend Integration
- Confirm response shape with frontend team
- Add CORS headers (`django-cors-headers`)
- Deploy to Render (Django app alongside existing DB)

### Milestone 6 — Deployment
- `DEBUG=False`, `ALLOWED_HOSTS`, static files via `whitenoise`
- Gunicorn + Render Web Service
- CI: GitHub Actions for lint + basic smoke tests

---

## Quick Start for New Developers

```bash
# 1. Clone
git clone https://github.com/preetishreddy/ex-cdi.git
cd ex-cdi

# 2. Virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Environment variables
cp .env.example .env
# Fill in DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT, SECRET_KEY, DEBUG

# 5. Run server
python manage.py runserver
# → http://127.0.0.1:8000/api/commits/
```
