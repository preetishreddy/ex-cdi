# API Documentation

Base URL: `http://127.0.0.1:8000/api`

---

## Starting the Server

```bash
cd C:\Users\preet\Projects\ex-cdi
venv\Scripts\activate
python manage.py runserver
```

---

## Environment Variables (.env)

There are two `.env` files in this project — only edit the one at the **project root**:

| File | Used by | Edit this? |
|------|---------|-----------|
| `/ex-cdi/.env` | Django API server (`manage.py runserver`) | YES — add all tokens here |
| `/ex-cdi/database/.env` | Old manual scripts (`extract_github.py` etc.) | No — only needed if running scripts manually |

Restart the server after any changes to `.env`.

```env
# Django
SECRET_KEY=your_django_secret_key
DEBUG=True

# Database
DB_NAME=project_knowledge
DB_USER=onboarding_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432

# Chatbot (AI)
# Get key: bytez.com → API Keys
BYTEZ_API_KEY=your_bytez_api_key

# GitHub
# Get token: GitHub → Settings → Developer Settings → Personal Access Tokens → Generate new token (needs repo scope)
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_OWNER=org_or_username           # e.g. mycompany
GITHUB_REPO=repository_name           # e.g. backend-api
GITHUB_MAX_COMMITS=100                 # how many commits to pull per sync

# Jira
# Get token: Atlassian Account → Security → Create and manage API tokens
JIRA_DOMAIN=yourcompany.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=PAY                   # your Jira project key
JIRA_MAX_ISSUES=500                    # how many tickets to pull per sync

# Confluence
# Uses same Atlassian API token as Jira
CONFLUENCE_DOMAIN=yourcompany.atlassian.net
CONFLUENCE_EMAIL=your@email.com
CONFLUENCE_API_TOKEN=your_confluence_api_token
CONFLUENCE_SPACE_ID=your_space_id      # numeric ID of the Confluence space
CONFLUENCE_SPACE_KEY=ONBOARD           # key shown in the Confluence URL
```

---

## API Overview

| Category | What it does |
|----------|-------------|
| **Read APIs** | Fetch data already stored in the database |
| **Ingest APIs** | Pull data from external sources (GitHub, Jira, Confluence) into the database |
| **Delete API** | Remove any record from the database |

---

## Read APIs

These return data already in the database. All are GET requests, no body needed.

---

### Test

| Method | URL |
|--------|-----|
| GET | `/api/test/` |

**Response:**
```json
{ "message": "hello preety" }
```

---

### Commits

#### List all commits
| Method | URL |
|--------|-----|
| GET | `/api/commits/` |

**Response:** Array of commit objects with files attached.

#### Get a single commit
| Method | URL |
|--------|-----|
| GET | `/api/commits/<sha>/` |

**URL param:** `sha` — the commit SHA (copy from the list response)

---

### Jira Tickets

#### List all tickets
| Method | URL |
|--------|-----|
| GET | `/api/tickets/` |

#### Get a single ticket
| Method | URL |
|--------|-----|
| GET | `/api/tickets/<issue_key>/` |

**URL param:** `issue_key` — e.g. `PAY-221`

#### Get a ticket with all linked data
| Method | URL |
|--------|-----|
| GET | `/api/tickets/<issue_key>/context/` |

**Response includes:** the ticket + any linked commits, Confluence pages, and meetings via entity references.

---

### Confluence Pages

#### List all pages
| Method | URL |
|--------|-----|
| GET | `/api/pages/` |

Returns lightweight list (no full content body).

#### Get a single page
| Method | URL |
|--------|-----|
| GET | `/api/pages/<uuid>/` |

**URL param:** `uuid` — copy from the list response
**Response includes:** full page content.

---

### Meetings

#### List all meetings
| Method | URL |
|--------|-----|
| GET | `/api/meetings/` |

Returns metadata only (no raw VTT transcript).

#### Get a single meeting
| Method | URL |
|--------|-----|
| GET | `/api/meetings/<uuid>/` |

**URL param:** `uuid` — copy from the list response
**Response includes:** everything + `raw_vtt_content` (full transcript).

---

### Projects

#### List all projects
| Method | URL |
|--------|-----|
| GET | `/api/projects/` |

#### Get a single project
| Method | URL |
|--------|-----|
| GET | `/api/projects/<uuid>/` |

**URL param:** `uuid` — copy from the list response

---

### Employees

#### List all employees
| Method | URL |
|--------|-----|
| GET | `/api/employees/` |

#### Get a single employee
| Method | URL |
|--------|-----|
| GET | `/api/employees/<uuid>/` |

**URL param:** `uuid` — copy from the list response

---

### Sprints

#### List all sprints
| Method | URL |
|--------|-----|
| GET | `/api/sprints/` |

#### Get a single sprint
| Method | URL |
|--------|-----|
| GET | `/api/sprints/<sprint_number>/` |

**URL param:** `sprint_number` — the sprint number e.g. `1`, `2`, `3`

#### Get all tickets in a sprint
| Method | URL |
|--------|-----|
| GET | `/api/sprints/<sprint_number>/tickets/` |

**Response includes:** all tickets with `is_completed`, `teammates`, and summary counts (total, completed, pending).

#### Get all meetings during a sprint
| Method | URL |
|--------|-----|
| GET | `/api/sprints/<sprint_number>/meetings/` |

**Response includes:** all meetings whose date falls within the sprint's start and end dates.

---

### Decisions

#### List all decisions
| Method | URL |
|--------|-----|
| GET | `/api/decisions/` |

**Optional query params:**
- `?category=architecture` — filter by category
- `?source_type=meeting` — filter by source (meeting, confluence, jira, git_commit)

#### Get a single decision
| Method | URL |
|--------|-----|
| GET | `/api/decisions/<uuid>/` |

**URL param:** `uuid` — copy from the list response

---

### Search

| Method | URL |
|--------|-----|
| GET | `/api/search/?q=<query>` |

**Query param:** `q` — the search term (add in Postman's Params tab)

Searches across: commit messages, ticket summaries/descriptions, page titles/content, meeting titles.

**Response:**
```json
{
    "query": "login",
    "commits": [...],
    "tickets": [...],
    "pages": [...],
    "meetings": [...]
}
```

---

## Chat API

The AI chatbot endpoint. Sends a natural-language question to the onboarding assistant and gets a response.

| Method | URL |
|--------|-----|
| POST | `/api/chat/` |

**How to send in Postman:**
1. Method: `POST`
2. URL: `http://127.0.0.1:8000/api/chat/`
3. Go to **Body** tab → select **raw** → change dropdown to **JSON**
4. Type the body (do not copy-paste — use straight quotes)
5. Click Send

**Request body — first message:**
```json
{
    "query": "Why did we choose React?"
}
```

**Request body — follow-up message (continue the conversation):**
```json
{
    "query": "Who made that decision?",
    "conversation_id": "89d58088-e5fe-4020-9e90-10cd4375bece"
}
```

Pass the `conversation_id` from the previous response to keep the bot in the same conversation. Omit it to start fresh.

**Response:**
```json
{
    "answer": "React was chosen because of the team's existing expertise...",
    "intent": "decision_query",
    "confidence": 0.85,
    "sources": ["decision:Use React for frontend", "meeting:Sprint 1 Planning"],
    "conversation_id": "89d58088-e5fe-4020-9e90-10cd4375bece",
    "turn": 1
}
```

| Field | Description |
|-------|-------------|
| `answer` | The AI's response text |
| `intent` | What the bot understood you were asking (decision_query, person_query, ticket_query, etc.) |
| `confidence` | How confident the intent classifier was (0–1) |
| `sources` | Which database records were used to generate the answer |
| `conversation_id` | Copy this into your next request to continue the conversation |
| `turn` | Which turn number this is in the conversation |

**Requires in `.env`:** `BYTEZ_API_KEY`

**Note:** Conversation history is stored in memory only. If the server restarts, all conversation history is lost and a new `conversation_id` must be used.

---

## Ingest APIs

These trigger a sync from an external source into the database. All are POST requests.
Reads config from `.env` — no request body needed (except meetings which requires a file).
Safe to run multiple times — will update existing records, not create duplicates.

---

### Ingest GitHub Commits

| Method | URL |
|--------|-----|
| POST | `/api/ingest/github/` |

**Requires in `.env`:** `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`
**Optional in `.env`:** `GITHUB_MAX_COMMITS` (default: 100)

**What it does:** Connects to GitHub API, pulls commits from the configured repo, saves them to the database. Creates entity references linking commits to any Jira ticket keys found in commit messages.

**Response:**
```json
{
    "source": "github",
    "repository": "mycompany/backend-api",
    "created": 5,
    "updated": 12,
    "errors": 0,
    "total": 17
}
```

---

### Ingest Jira Tickets

| Method | URL |
|--------|-----|
| POST | `/api/ingest/jira/` |

**Requires in `.env`:** `JIRA_DOMAIN`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
**Optional in `.env`:** `JIRA_PROJECT_KEY` (default: PAY), `JIRA_MAX_ISSUES` (default: 500)

**What it does:** Connects to Jira API, pulls all tickets from the configured project, saves them to the database. Creates entity references for epic links.

**Response:**
```json
{
    "source": "jira",
    "project": "PAY",
    "created": 10,
    "updated": 45,
    "errors": 0,
    "total": 55
}
```

---

### Ingest Confluence Pages

| Method | URL |
|--------|-----|
| POST | `/api/ingest/confluence/` |

**Requires in `.env`:** `CONFLUENCE_DOMAIN`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN`, `CONFLUENCE_SPACE_ID`
**Optional in `.env`:** `CONFLUENCE_SPACE_KEY` (default: ONBOARD)

**What it does:** Connects to Confluence API, pulls all pages from the configured space, converts HTML to Markdown, saves to the database. Creates entity references for any Jira ticket keys found in page content.

**Response:**
```json
{
    "source": "confluence",
    "space": "ONBOARD",
    "created": 3,
    "updated": 8,
    "errors": 0,
    "total": 11
}
```

---

### Ingest Meeting (VTT file upload)

| Method | URL |
|--------|-----|
| POST | `/api/ingest/meetings/` |

**No `.env` vars needed.**

**How to send in Postman:**
1. Method: `POST`
2. URL: `http://127.0.0.1:8000/api/ingest/meetings/`
3. Go to **Body** tab → select **form-data**
4. Add a row: Key = `file`, change type dropdown to **File**, upload your `.vtt` file
5. Click Send

**What it does:** Reads the uploaded VTT transcript, extracts speakers and duration, saves the meeting to the database. Creates entity references for any Jira ticket keys mentioned in the transcript.
Uploading the same filename again will **update** the existing record, not create a duplicate.

**Response:**
```json
{
    "source": "meeting",
    "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "2026-01-15 Standup",
    "created": true,
    "participants": 5,
    "duration_seconds": 1800,
    "ticket_references_created": 2
}
```

> `"created": true` means a new record was created. `"created": false` means an existing record was updated.

---

## Delete API

One common endpoint to delete any record from the database.

| Method | URL |
|--------|-----|
| DELETE | `/api/delete/<entity_type>/<id>/` |

### entity_type and id reference

| What to delete | `entity_type` | `id` to use | Example |
|----------------|--------------|-------------|---------|
| Commit | `commits` | SHA | `a3f9c12ef...` |
| Jira Ticket | `tickets` | Issue key | `PAY-221` |
| Confluence Page | `pages` | UUID | `550e8400-...` |
| Meeting | `meetings` | UUID | `550e8400-...` |
| Project | `projects` | UUID | `550e8400-...` |
| Employee | `employees` | UUID | `550e8400-...` |
| Sprint | `sprints` | UUID | `550e8400-...` |
| Decision | `decisions` | UUID | `550e8400-...` |

### How to use in Postman
1. Method: `DELETE`
2. Build the URL using the table above, e.g.:
   - `http://127.0.0.1:8000/api/delete/meetings/550e8400-e29b-41d4-a716-446655440000/`
   - `http://127.0.0.1:8000/api/delete/tickets/PAY-221/`
   - `http://127.0.0.1:8000/api/delete/commits/a3f9c12.../`
3. No body needed
4. Click Send

**Response:**
```json
{ "deleted": true, "entity_type": "meetings", "id": "550e8400-..." }
```

**Error — wrong entity type:**
```json
{ "error": "Unknown entity type \"foo\". Choose from: commits, tickets, pages, meetings, projects" }
```

---

## Common Errors

| Status | Message | Fix |
|--------|---------|-----|
| `400` | `GITHUB_TOKEN not set in environment` | Add `GITHUB_TOKEN` to `.env` and restart server |
| `400` | `GITHUB_OWNER and GITHUB_REPO must be set` | Add both to `.env` and restart server |
| `400` | `No file uploaded` | In Postman Body → form-data, set key `file` with type File |
| `400` | `File must be a .vtt file` | Make sure you are uploading a `.vtt` file |
| `400` | `Unknown entity type` | Check spelling — valid types are: commits, tickets, pages, meetings, projects |
| `404` | Not Found | The ID doesn't exist — use the list endpoint first to get valid IDs |
| `500` | Internal Server Error | Check the terminal running `runserver` for the full traceback |

---

## Notes

- Always include the **trailing slash** in URLs — e.g. `/api/ingest/meetings/` not `/api/ingest/meetings`
- Ingest endpoints are **synchronous** — Postman will wait until the sync is fully complete before showing the response. Large syncs (500 Jira tickets) may take a few minutes.
- Ingest endpoints use **update_or_create** — running them multiple times is safe, it won't create duplicates.
