# Onboarding AI Project - Complete Summary

> **Single Source of Truth** - Everything done from project inception to current state
> 
> **Last Updated:** March 2026 | **Version:** 3.0.0

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Timeline & Phases](#2-timeline--phases)
3. [Database Architecture](#3-database-architecture)
4. [Synthetic Data Generation](#4-synthetic-data-generation)
5. [Data Processing Pipeline](#5-data-processing-pipeline)
6. [Chatbot Implementation](#6-chatbot-implementation)
7. [Technology Stack](#7-technology-stack)
8. [File Structure](#8-file-structure)
9. [Key Decisions Made](#9-key-decisions-made)
10. [Issues Encountered & Solutions](#10-issues-encountered--solutions)
11. [Current State & Known Issues](#11-current-state--known-issues)
12. [Future Considerations](#12-future-considerations)
13. [Quick Reference](#13-quick-reference)

---

## 1. Project Overview

### Purpose

Build an **AI-powered chatbot** that helps team members understand the Employee Onboarding Portal project by:
- Answering questions about project decisions and their rationale
- Tracking who worked on what
- Providing sprint summaries and status updates
- Explaining technical architecture and setup procedures
- Retrieving meeting discussions and action items

### Core Concept

Instead of a general-purpose chatbot, this is a **knowledge-grounded conversational assistant** that:
1. Retrieves relevant data from a PostgreSQL database
2. Uses that data as context for GPT-4o
3. Generates accurate answers based ONLY on retrieved information
4. Maintains conversation history for multi-turn interactions

### The "Fake" Project

The chatbot answers questions about a **synthetic project** called the "Employee Onboarding Portal" - a web application for managing employee onboarding tasks. This synthetic project has:
- 2 sprints of development
- 6 team members
- Technical decisions (React, Django, PostgreSQL, etc.)
- Meeting transcripts, commits, tickets, documentation

---

## 2. Timeline & Phases

### Phase 1: Database Setup (Feb 23-25, 2026)

| Session | What Was Done |
|---------|---------------|
| Feb 23 | PostgreSQL installation, Django project setup, initial schema design |
| Feb 25 | Complete database setup, API configuration, backend documentation |

**Deliverables:**
- Django project in `database/` folder
- PostgreSQL database schema
- Models for: git_commits, meetings, jira_tickets, confluence_pages

### Phase 2: Data Extraction Scripts (Feb 27, 2026)

| Session | What Was Done |
|---------|---------------|
| Morning | GitHub, Confluence, Jira extraction scripts |
| Afternoon | Render cloud deployment, employees table |
| Evening | Synthetic data generation (VTT, CSV, Markdown) |

**Deliverables:**
- `scripts/extract_commits.py`
- `scripts/extract_confluence.py`
- `scripts/extract_jira.py`
- Synthetic VTT meeting files
- Synthetic Confluence markdown pages
- Synthetic Jira tickets CSV
- Synthetic git commits

### Phase 3: LLM Processing (Mar 2, 2026)

| Session | What Was Done |
|---------|---------------|
| Session 1 | DSPy-style meeting summarization |
| Session 2 | Decision extraction system setup |
| Session 3 | Complete decision extraction with deduplication |

**Deliverables:**
- `scripts/summarize_meetings.py` - Populates meeting summaries
- `scripts/extract_decisions.py` - Extracts decisions to unified table
- `decisions` table with 15+ decisions
- Supersession detection (newer decisions replacing older ones)

### Phase 4: Chatbot Implementation (Mar 3-4, 2026)

| Session | What Was Done |
|---------|---------------|
| Mar 3 | Phase 1 chatbot - Single-turn Q&A |
| Mar 4 Morning | Conversational upgrade - Multi-turn with memory |
| Mar 4 Afternoon | Sprint summary feature, demo questions |

**Deliverables:**
- `chatbot/` module with full pipeline
- Intent classification (9 types)
- SQL retrieval from all tables
- Context building with templates
- Bytez LLM integration (GPT-4o)
- Conversation history with reference resolution

### Phase 5: Bug Fixes & Enhancements (Mar 5-6, 2026)

| Session | What Was Done |
|---------|---------------|
| Validation 1 | Found context drift, Sprint 2 status issues |
| Validation 2 | Found person query failures, topic command broken |
| Fixes | v3.0.0 with person queries, list support, hallucination prevention |

**Deliverables:**
- Fixed topic CLI command
- Role-to-person mapping (frontend → Lisa Park)
- Person summary documents
- List query support
- Hallucination prevention
- Comprehensive documentation

---

## 3. Database Architecture

### Hosting

| Setting | Value |
|---------|-------|
| Provider | Render.com |
| Database | PostgreSQL 14 |
| Region | Oregon (US West) |
| Connection | SSL required |

### Schema (11 Tables)

```
┌─────────────────────────────────────────────────────────────┐
│                     DATABASE SCHEMA                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   meetings   │     │  decisions   │     │  employees   │ │
│  │──────────────│     │──────────────│     │──────────────│ │
│  │ id           │     │ id           │     │ id           │ │
│  │ title        │────▶│ source_type  │     │ name         │ │
│  │ meeting_date │     │ source_title │     │ email        │ │
│  │ summary      │     │ title        │     │ role         │ │
│  │ key_decisions│     │ rationale    │     │ department   │ │
│  │ action_items │     │ alternatives │     │ start_date   │ │
│  │ raw_vtt      │     │ decided_by   │     └──────────────┘ │
│  └──────────────┘     │ supersedes   │                      │
│                       │ superseded_by│                      │
│  ┌──────────────┐     └──────────────┘                      │
│  │ git_commits  │                                           │
│  │──────────────│     ┌──────────────┐     ┌──────────────┐ │
│  │ sha          │     │    sprints   │     │sprint_tickets│ │
│  │ author_name  │     │──────────────│     │──────────────│ │
│  │ message      │     │ sprint_number│◀────│ sprint_id    │ │
│  │ commit_date  │     │ name         │     │ ticket_id    │──┐
│  │ related_tix  │     │ start_date   │     └──────────────┘  │
│  └──────────────┘     │ end_date     │                       │
│                       │ goal         │     ┌──────────────┐  │
│  ┌──────────────┐     └──────────────┘     │ jira_tickets │  │
│  │ confluence   │                          │──────────────│  │
│  │   _pages     │                          │ issue_key    │◀─┘
│  │──────────────│     ┌──────────────┐     │ summary      │
│  │ title        │     │   entity_    │     │ status       │
│  │ content      │     │  references  │     │ assignee     │
│  │ author       │     │──────────────│     │ reporter     │
│  │ labels       │     │ source_type  │     │ sprint       │
│  └──────────────┘     │ entity_type  │     └──────────────┘
│                       │ entity_value │                      │
│                       └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Table Purposes

| Table | Records | Purpose |
|-------|---------|---------|
| `decisions` | 15 | Unified decision timeline from all sources |
| `meetings` | 5 | Meeting transcripts with AI-generated summaries |
| `jira_tickets` | 21 | Sprint tickets with status, assignee |
| `confluence_pages` | 6 | Documentation pages |
| `git_commits` | 32 | Commit history with authors |
| `sprints` | 2 | Sprint metadata (dates, goals) |
| `sprint_tickets` | 20 | Maps tickets to sprints |
| `employees` | 6 | Team member info |
| `entity_references` | - | Cross-references between entities |

---

## 4. Synthetic Data Generation

### The Fake Project: Employee Onboarding Portal

**Concept:** A web application where:
- HR creates onboarding task templates
- Managers assign tasks to new employees
- Employees track their onboarding progress
- System sends reminders for incomplete tasks

### Team Members

| Name | Role | Focus Area |
|------|------|------------|
| Sarah Chen | Tech Lead | Architecture, database |
| Marcus Thompson | Backend Developer | Django, API, auth |
| Lisa Park | Frontend Developer | React, UI components |
| Priya Sharma | QA Engineer | Testing |
| James O'Brien | DevOps | CI/CD, deployment |
| Dave Rossi | Product Manager | Requirements |

### Sprint Data

#### Sprint 1: Foundation (Jan 5-16, 2026)

**Goal:** Build foundation - database schema, authentication, basic UI

**Key Decisions:**
- Use Django for backend (team expertise)
- Use React for frontend (component-based)
- Use PostgreSQL (Django ORM compatibility)
- Use JWT for authentication (stateless, scalable)
- Use AWS for deployment (existing infrastructure)
- Switch from Material UI to Tailwind CSS (flexibility)

**Tickets:** ONBOARD-11 through ONBOARD-20 (10 tickets, 8 completed)

#### Sprint 2: Core Features (Jan 17-31, 2026)

**Goal:** Build core features - task management, employee views, notifications

**Key Decisions:**
- Add SQLAlchemy Core for complex queries
- Use ECS Fargate for deployment
- Implement role-based access control

**Tickets:** ONBOARD-21 through ONBOARD-30 (10 tickets, all completed)

### Generated Files

| Type | Count | Location |
|------|-------|----------|
| VTT Meeting Files | 5 | `synthetic_data/vtt/` |
| Confluence Pages | 6 | `synthetic_data/confluence/` |
| Jira Tickets CSV | 1 (21 tickets) | `synthetic_data/jira/` |
| Git Commits | 32 | `synthetic_data/commits.json` |

---

## 5. Data Processing Pipeline

### Step 1: Ingest Raw Data

```bash
# Ingest all data types
python manage.py ingest_confluence ../synthetic_data/confluence/
python manage.py ingest_jira ../synthetic_data/jira/tickets.csv
python manage.py ingest_commits ../synthetic_data/commits.json
python manage.py ingest_vtt ../synthetic_data/vtt/
```

### Step 2: Summarize Meetings (LLM)

```bash
python scripts/summarize_meetings.py
```

**What it does:**
- Takes raw VTT content
- Sends to GPT-4o via Bytez API
- Extracts: summary, key_decisions, action_items
- Updates meeting records

**LLM Calls:** 5 (one per meeting)

### Step 3: Extract Decisions (LLM)

```bash
python scripts/extract_decisions.py
```

**What it does:**
- Processes meetings, confluence, jira, commits
- Extracts decisions with: title, rationale, alternatives, impact
- Detects supersession (newer replacing older)
- Deduplicates across sources
- Populates unified `decisions` table

**LLM Calls:** ~32 (varies by content)

### Processing Statistics

| Step | LLM Calls | Cost (approx) |
|------|-----------|---------------|
| Meeting summarization | 5 | $0.15 |
| Decision extraction | 32 | $0.96 |
| **Total setup** | **37** | **~$1.11** |
| Runtime (per query) | 1 | ~$0.03 |

---

## 6. Chatbot Implementation

### Architecture: Structured Context Injection

```
┌─────────────────────────────────────────────────────────────┐
│                      USER QUERY                              │
│              "Why did we choose React?"                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 CONVERSATION HISTORY                         │
│  • Track previous messages                                   │
│  • Resolve references ("it", "that", "they")                │
│  • Track current topic                                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  INTENT CLASSIFIER                           │
│  • Rule-based keyword matching                              │
│  • 9 intent types                                           │
│  • Entity extraction (names, ticket IDs, tech terms)        │
│  • Role-to-person mapping                                   │
│                                                              │
│  Output: decision_query, entities=['react', 'frontend']     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQL RETRIEVER                             │
│  • Route by intent type                                     │
│  • Django ORM queries                                       │
│  • No vector embeddings - keyword matching                  │
│                                                              │
│  Query: SELECT * FROM decisions                             │
│         WHERE title ILIKE '%react%'                         │
│         OR rationale ILIKE '%react%'                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   CONTEXT BUILDER                            │
│  • Format documents into text                               │
│  • Add conversation history                                 │
│  • Apply intent-specific templates                          │
│  • Add anti-hallucination instructions                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLM (GPT-4o)                               │
│  • Bytez API                                                │
│  • Generate response from context only                      │
│  • If no context, say "I don't know"                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       RESPONSE                               │
│  "React was chosen for its component-based architecture..." │
└─────────────────────────────────────────────────────────────┘
```

### Why NOT RAG?

We chose **Structured Context Injection** over traditional RAG because:

| RAG Approach | Our Approach |
|--------------|--------------|
| Embed all text → vector DB | Store structured data in PostgreSQL |
| Semantic search → similar chunks | Intent classification → targeted SQL |
| May retrieve irrelevant chunks | Retrieves exactly what's needed |
| Expensive embedding costs | No embedding costs |
| Complex infrastructure | Simple Django ORM |

**Key Insight:** Our data is already structured (tables with relationships). SQL queries are more precise than semantic search for structured data.

### Intent Types

| Intent | Trigger Keywords | Retrieval Method |
|--------|------------------|------------------|
| `DECISION_QUERY` | why, decision, chose | `_retrieve_decisions()` |
| `PERSON_QUERY` | who, worked, Marcus | `_retrieve_person_info()` |
| `TIMELINE_QUERY` | when, history, timeline | `_retrieve_timeline()` |
| `HOWTO_QUERY` | how, setup, configure | `_retrieve_documentation()` |
| `STATUS_QUERY` | status, progress, blocked | `_retrieve_status()` |
| `TICKET_QUERY` | ONBOARD-XX, ticket | `_retrieve_ticket_info()` |
| `MEETING_QUERY` | meeting, discussed | `_retrieve_meetings()` |
| `SPRINT_SUMMARY_QUERY` | sprint summary, overview | `_retrieve_sprint_summary()` |
| `GENERAL_QUERY` | (fallback) | `_retrieve_general()` |

### Conversation Features

| Feature | Implementation |
|---------|----------------|
| Multi-turn memory | Store last 10 exchanges |
| Reference resolution | "it" → current topic |
| Topic tracking | `current_topic`, `topic_stack` |
| Follow-up context | Track entities from last response |
| Role mapping | "frontend" → Lisa Park |

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Mar 3 | Single-turn Q&A |
| 2.0.0 | Mar 4 | Multi-turn conversations, sprint summaries |
| 3.0.0 | Mar 6 | Person queries, list support, hallucination prevention |

---

## 7. Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| Database | PostgreSQL 14 | Structured data storage |
| Backend Framework | Django 5.x | ORM, models, management commands |
| LLM | GPT-4o | Response generation |
| LLM API | Bytez | API wrapper for GPT-4o |
| Language | Python 3.10+ | All code |

### Python Packages

```
django>=5.0
psycopg2-binary
python-dotenv
requests
```

### External Services

| Service | Purpose | Cost |
|---------|---------|------|
| Render.com | PostgreSQL hosting | Free tier |
| Bytez API | GPT-4o access | ~$0.03/query |

---

## 8. File Structure

```
Onboarding_AI/
├── database/                      # Django project
│   ├── manage.py
│   ├── .env                       # Database credentials
│   ├── database/                  # Django settings
│   │   ├── settings.py
│   │   └── urls.py
│   ├── knowledge_base/            # Django app
│   │   ├── models.py              # All 11 models
│   │   ├── admin.py
│   │   └── management/
│   │       └── commands/          # Ingestion commands
│   │           ├── ingest_commits.py
│   │           ├── ingest_confluence.py
│   │           ├── ingest_jira.py
│   │           └── ingest_vtt.py
│   └── scripts/                   # LLM processing
│       ├── summarize_meetings.py
│       └── extract_decisions.py
│
├── chatbot/                       # Chatbot module
│   ├── __init__.py
│   ├── main.py                    # Orchestrator + ConversationHistory
│   ├── django_setup.py            # Django config for chatbot
│   ├── README.md                  # Technical documentation
│   ├── intent/                    # Classification
│   │   ├── __init__.py
│   │   ├── types.py               # IntentType enum
│   │   └── classifier.py          # Classification logic
│   ├── retriever/                 # Data retrieval
│   │   ├── __init__.py
│   │   ├── base.py                # Document class
│   │   └── sql_retriever.py       # SQL queries
│   ├── context/                   # Context building
│   │   ├── __init__.py
│   │   ├── templates.py           # Prompt templates
│   │   └── builder.py             # Context formatting
│   └── llm/                       # LLM interface
│       ├── __init__.py
│       └── bytez_llm.py           # Bytez API wrapper
│
├── docs/                          # Documentation
│   ├── DATABASE.md
│   ├── BACKEND_DEVELOPER_GUIDE.md
│   └── CHATBOT_SETUP_GUIDE.md
│
├── synthetic_data/                # Generated test data
│   ├── vtt/                       # Meeting transcripts
│   ├── confluence/                # Documentation pages
│   ├── jira/                      # Tickets CSV
│   └── commits.json               # Git commits
│
├── test_conversational.py         # Chatbot test suite
├── requirements.txt
└── README.md
```

---

## 9. Key Decisions Made

### Database Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| PostgreSQL | Django ORM compatibility, relational data | MongoDB, SQLite |
| Render hosting | Free tier, easy setup | AWS RDS, local |
| Unified decisions table | Single source for all decisions | Separate per source |
| Supersession tracking | Show decision evolution | Ignore old decisions |

### Chatbot Architecture Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Structured Context Injection | Data already structured, SQL more precise | RAG with vector DB |
| Rule-based intent classification | Simple, interpretable, no training needed | ML classifier, LLM classification |
| Django ORM retrieval | Reuse existing models, no new infrastructure | Raw SQL, separate DB connection |
| Bytez API | Simple API, GPT-4o access | Direct OpenAI, Anthropic |
| Keyword matching | Sufficient for structured queries | Semantic search, embeddings |

### Chatbot Feature Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| 10-turn history limit | Balance context vs tokens | Unlimited, 5 turns |
| Role-to-person hardcoding | Quick solution, works for fixed team | Dynamic DB lookup |
| Hallucination prevention | Trust critical for knowledge system | Let LLM fill gaps |
| Person summary documents | Better UX for "who worked on X" | Raw data only |

---

## 10. Issues Encountered & Solutions

### Database Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| PostgreSQL install fails (macOS) | Homebrew path issues | `brew install postgresql@14`, add to PATH |
| Django can't connect | Missing SSL | Add `sslmode=require` to connection |
| Migration errors | Model changes | `makemigrations`, `migrate` |
| Naive datetime warnings | Timezone not set | Use `timezone.now()` or make aware |

### Chatbot Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: django` | venv not activated | `source venv/bin/activate` |
| Import errors in chatbot | Wrong relative imports | Fixed `__init__.py` exports |
| Sprint 2 status empty | All tickets "Done", only queried open | Query ALL tickets for sprint |
| Context drift | Topic not persisted | Added `topic_stack`, priority to inferred entities |
| Person queries empty | Name matching too strict | Added `KNOWN_PERSONS`, first-name search |
| "topic" command fails | Processed as query | Check CLI commands BEFORE `chat()` |
| Hallucination | LLM invents when no context | Added `_generate_no_info_response()` |
| Follow-up fails | Entities from response not tracked | Added `last_response_entities` |

### LLM Processing Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Task completions as decisions | Prompt too broad | Added exclusion rules in prompt |
| Duplicate decisions | Same decision in multiple sources | Deduplication by title similarity |
| Missing fields | Prompt didn't request all fields | Updated prompt with all required fields |

---

## 11. Current State & Known Issues

### What's Working ✅

| Feature | Status |
|---------|--------|
| Decision queries | ✅ Working |
| Person queries (by name) | ✅ Working |
| Role-based queries | ✅ Working (frontend → Lisa) |
| Sprint summaries | ✅ Working |
| Sprint status | ✅ Working (shows completion %) |
| Ticket queries | ✅ Working |
| Meeting queries | ✅ Working |
| Documentation queries | ✅ Working |
| List queries | ✅ Working |
| Multi-turn conversations | ✅ Working |
| Reference resolution | ✅ Working |
| Topic tracking | ✅ Working |
| CLI commands | ✅ Working |

### Known Limitations ⚠️

| Limitation | Impact | Potential Fix |
|------------|--------|---------------|
| Hardcoded person names | New team = code change | Dynamic DB lookup |
| Hardcoded role mapping | Role changes = code change | Query employees table |
| No semantic search | May miss relevant content | Add embeddings (optional) |
| Single session memory | Memory clears on restart | Persist to DB (optional) |
| English only | No i18n support | Add translation layer |

### Current Hardcoded Values

```python
# In main.py
ROLE_PERSON_MAPPING = {
    'frontend': ['Lisa Park'],
    'backend': ['Marcus Thompson'],
    ...
}

# In classifier.py
PERSON_NAMES = ['sarah', 'marcus', 'lisa', 'priya', 'james', 'dave']

# In sql_retriever.py
KNOWN_PERSONS = {
    'sarah': 'Sarah Chen',
    'marcus': 'Marcus Thompson',
    ...
}
```

---

## 12. Future Considerations

### Short-term Improvements

1. **Dynamic Person Resolution**
   - Query `employees` table at startup
   - Query `git_commits` for author names
   - Cache results, refresh periodically

2. **Configuration File**
   - Move hardcoded values to `chatbot_config.yaml`
   - Allow overrides without code changes

3. **Better Error Messages**
   - More specific "not found" messages
   - Suggest alternative queries

### Medium-term Enhancements

1. **API Endpoint**
   - Flask/FastAPI wrapper
   - Session management
   - Rate limiting

2. **Web Interface**
   - React chat UI
   - Conversation persistence
   - Source highlighting

3. **Analytics**
   - Track query patterns
   - Identify knowledge gaps
   - Measure response quality

### Long-term Vision

1. **Multi-Project Support**
   - Separate knowledge bases per project
   - Project-specific prompts

2. **Real Data Integration**
   - Connect to real Jira/Confluence/GitHub
   - Incremental updates

3. **Advanced Features**
   - Proactive suggestions
   - Onboarding flow guidance
   - Knowledge gap detection

---

## 13. Quick Reference

### Common Commands

```bash
# Activate environment
cd ~/Desktop/Onboarding_AI
source venv/bin/activate

# Run chatbot
cd chatbot
python main.py

# Run tests
cd ~/Desktop/Onboarding_AI
python test_conversational.py --interactive

# Database shell
cd database
python manage.py shell

# Git push
git add . && git commit -m "message" && git push origin chatbot
```

### Database Queries (Django Shell)

```python
from knowledge_base.models import *

# Count records
Decision.objects.count()
Meeting.objects.count()
JiraTicket.objects.count()

# Find person's work
GitCommit.objects.filter(author_name__icontains='marcus')
JiraTicket.objects.filter(assignee__icontains='lisa')

# Sprint tickets
SprintTicket.objects.filter(sprint__sprint_number=1)
```

### Chatbot CLI Commands

| Command | Action |
|---------|--------|
| `quit` | Exit |
| `help` | Show examples |
| `clear` | Clear history |
| `debug` | Toggle verbose |
| `topic` | Show current topic |
| `status` | Show bot health |

### Key File Locations

| Purpose | File |
|---------|------|
| Main chatbot | `chatbot/main.py` |
| Intent classification | `chatbot/intent/classifier.py` |
| SQL retrieval | `chatbot/retriever/sql_retriever.py` |
| Database models | `database/knowledge_base/models.py` |
| Django settings | `database/database/settings.py` |
| Technical docs | `chatbot/README.md` |
| User guide | `docs/CHATBOT_SETUP_GUIDE.md` |

### API Keys & Credentials

| Item | Location |
|------|----------|
| Database URL | `database/.env` |
| Bytez API Key | Hardcoded in `bytez_llm.py` |

---

## Appendix: Session Links

| Date | Topic | Transcript |
|------|-------|------------|
| Feb 23 | PostgreSQL/Django setup | `2026-02-23-22-45-58-postgres-django-db-setup.txt` |
| Feb 25 | Database completion | `2026-02-25-20-09-04-onboarding-ai-database-setup.txt` |
| Feb 27 | Extraction scripts | `2026-02-27-15-18-57-database-extraction-scripts-setup.txt` |
| Feb 27 | Render deployment | `2026-02-27-19-05-47-onboarding-ai-database-render-deployment.txt` |
| Feb 27 | Synthetic data | `2026-02-27-22-35-36-onboarding-synthetic-data-generation.txt` |
| Mar 2 | Meeting summarization | `2026-03-02-16-36-19-dspy-meeting-summarization-setup.txt` |
| Mar 2 | Decision extraction setup | `2026-03-02-17-50-39-dspy-decision-extraction-setup.txt` |
| Mar 2 | Decision extraction complete | `2026-03-02-22-46-47-dspy-decision-extraction-complete.txt` |
| Mar 3 | Chatbot Phase 1 | `2026-03-03-02-06-22-chatbot-phase1-implementation.txt` |
| Mar 4 | Conversational upgrade | `2026-03-04-00-02-02-chatbot-conversational-upgrade.txt` |
| Mar 4 | Sprint summaries | `2026-03-04-03-25-43-chatbot-sprint-summary-feature.txt` |

---

*This document serves as the single source of truth for the Onboarding AI project.*
*Last updated: March 2026*
