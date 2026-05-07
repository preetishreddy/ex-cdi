# Onboarding AI Chatbot - Technical Documentation

> **Version 3.0.0** - Conversational Chatbot with Enhanced Person Queries & List Support

This document provides detailed technical documentation for the Onboarding AI Chatbot system.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Folder Structure](#folder-structure)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Intent Types](#intent-types)
7. [Retrieval Methods](#retrieval-methods)
8. [Conversation Features](#conversation-features)
9. [Configuration](#configuration)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)
12. [Version History](#version-history)

---

## Overview

The Onboarding AI Chatbot is a **conversational assistant** that helps team members understand the Employee Onboarding Portal project. It maintains conversation history, resolves references, and retrieves information from multiple data sources.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-turn Conversations** | Remembers previous messages in a session |
| **Reference Resolution** | Understands "it", "that", "they", "who wrote it" from context |
| **Intent Classification** | 9 query types with automatic detection |
| **Person Queries** | Find who worked on what, role-based lookups |
| **List Queries** | List all Confluence pages, decisions, meetings |
| **Sprint Summaries** | Real-time aggregation of sprint data |
| **Database Retrieval** | Direct PostgreSQL queries via Django ORM |
| **GPT-4o Responses** | Powered by Bytez API |
| **Hallucination Prevention** | Won't make up information not in context |

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Django 5.x |
| Database | PostgreSQL (Render) |
| LLM Provider | Bytez API (GPT-4o) |
| Language | Python 3.10+ |

---

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER QUERY                                      │
│                     "Who worked on the frontend?"                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     0. CONVERSATION HISTORY                                  │
│                                                                              │
│   • Check previous messages for context                                      │
│   • Resolve references ("it", "that", "who wrote it")                       │
│   • Track current topic and entities                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         1. INTENT CLASSIFIER                                 │
│                                                                              │
│   • Classify query type (person_query, decision_query, etc.)                │
│   • Extract entities (names, ticket IDs, tech terms)                        │
│   • Map roles to people (frontend → Lisa Park)                              │
│                                                                              │
│   Output: IntentType.PERSON_QUERY, entities=['Lisa Park']                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          2. SQL RETRIEVER                                    │
│                                                                              │
│   • Route to appropriate retrieval method                                   │
│   • Execute Django ORM queries                                              │
│   • Create summary documents for people/sprints                             │
│                                                                              │
│   Output: [Document(person_summary), Document(commits), ...]                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         3. CONTEXT BUILDER                                   │
│                                                                              │
│   • Format documents into structured context                                │
│   • Add conversation history                                                │
│   • Add last response for follow-up context                                 │
│   • Apply intent-specific templates                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            4. LLM (Bytez)                                    │
│                                                                              │
│   • Send prompt with anti-hallucination rules                               │
│   • Generate response based ONLY on context                                 │
│   • If no context found, return honest "I don't know"                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         5. UPDATE HISTORY                                    │
│                                                                              │
│   • Store user query + assistant response                                   │
│   • Extract entities mentioned in response                                  │
│   • Update current topic for follow-ups                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
chatbot/
├── __init__.py              # Package exports (v3.0.0)
├── main.py                  # Main orchestrator + ConversationHistory
├── django_setup.py          # Django configuration for database access
├── README.md                # This file
│
├── intent/                  # Intent Classification Module
│   ├── __init__.py
│   ├── types.py             # IntentType enum + configurations
│   └── classifier.py        # Classification logic + entity extraction
│
├── retriever/               # Data Retrieval Module
│   ├── __init__.py
│   ├── base.py              # Abstract interface + Document class
│   └── sql_retriever.py     # PostgreSQL retrieval with person/list support
│
├── context/                 # Context Building Module
│   ├── __init__.py
│   ├── templates.py         # System prompts + intent templates
│   └── builder.py           # Context formatting with history support
│
└── llm/                     # LLM Interface Module
    ├── __init__.py
    └── bytez_llm.py         # Bytez API wrapper (GPT-4o)
```

---

## Core Components

### 1. Main Orchestrator (`main.py`)

#### Key Classes

| Class | Purpose |
|-------|---------|
| `Message` | Single message with role, content, entities, topic |
| `ConversationHistory` | Manages multi-turn memory and reference resolution |
| `ChatResponse` | Structured response with answer, intent, sources |
| `OnboardingChatbot` | Main chatbot class orchestrating all components |

#### Role-Person Mapping

```python
ROLE_PERSON_MAPPING = {
    'frontend': ['Lisa Park'],
    'backend': ['Marcus Thompson'],
    'database': ['Sarah Chen', 'Marcus Thompson'],
    'devops': ['Dave Rossi'],
    'authentication': ['Marcus Thompson'],
    ...
}
```

#### Key Methods

```python
class OnboardingChatbot:
    def chat(query) -> ChatResponse      # Full pipeline with history
    def chat_simple(query) -> str        # Just the answer
    def clear_history()                   # Reset conversation
    def get_current_topic() -> str        # Current topic being discussed
    def get_current_entities() -> List    # Current entities in context
    def health_check() -> dict            # Component status
```

#### CLI Commands

| Command | Description |
|---------|-------------|
| `quit` | Exit the chatbot |
| `help` | Show example questions |
| `clear` | Clear conversation history |
| `debug` | Toggle verbose mode |
| `topic` | Show current topic and entities |
| `status` | Show bot health status |

---

### 2. Intent Classifier (`intent/classifier.py`)

#### Detection Methods

| Method | Purpose |
|--------|---------|
| `_is_person_query()` | Detect person names, roles, "who" questions |
| `_is_sprint_summary_query()` | Detect sprint summary requests |
| `_is_list_query()` | Detect "list all X" requests |
| `_extract_entities()` | Extract ticket IDs, names, tech terms |

#### Person Query Detection

Detects:
- Direct names: "What has Marcus been working on?"
- Role keywords: "Who worked on the frontend?"
- Possessive patterns: "Show me Lisa's commits"
- Contact queries: "Who should I contact for backend?"

```python
PERSON_NAMES = ['sarah', 'marcus', 'lisa', 'priya', 'james', 'dave', ...]
ROLE_KEYWORDS = ['frontend', 'backend', 'api', 'database', 'devops', ...]
```

---

### 3. SQL Retriever (`retriever/sql_retriever.py`)

#### Retrieval Methods

| Intent | Method | Tables |
|--------|--------|--------|
| `decision_query` | `_retrieve_decisions()` | decisions |
| `person_query` | `_retrieve_person_info()` | commits, tickets, decisions |
| `timeline_query` | `_retrieve_timeline()` | decisions, meetings |
| `howto_query` | `_retrieve_documentation()` | confluence_pages |
| `status_query` | `_retrieve_status()` | jira_tickets, sprints |
| `ticket_query` | `_retrieve_ticket_info()` | jira_tickets, commits |
| `meeting_query` | `_retrieve_meetings()` | meetings |
| `sprint_summary_query` | `_retrieve_sprint_summary()` | all tables aggregated |
| `list queries` | `_retrieve_list()` | varies |

#### Person Query Flow

```
"Who worked on frontend?" 
    │
    ▼
Detect role keyword "frontend"
    │
    ▼
Map to person: Lisa Park
    │
    ▼
Query commits: WHERE author_name ILIKE '%Lisa%'
Query tickets: WHERE assignee ILIKE '%Lisa%'
Query decisions: WHERE decided_by ILIKE '%Lisa%'
    │
    ▼
Create person summary document
    │
    ▼
Return [summary, commits, tickets, decisions]
```

#### List Query Support

```python
def _retrieve_list(query, entities, limit):
    if 'confluence' in query or 'page' in query:
        # Return all Confluence pages with summary
    elif 'decision' in query:
        # Return all active decisions with summary
    elif 'meeting' in query:
        # Return all meetings with summary
```

#### Known Persons Mapping

```python
KNOWN_PERSONS = {
    'sarah': 'Sarah Chen',
    'marcus': 'Marcus Thompson',
    'lisa': 'Lisa Park',
    'priya': 'Priya Sharma',
    'james': "James O'Brien",
    'dave': 'Dave Rossi',
}
```

---

### 4. Conversation History

#### Features

| Feature | Implementation |
|---------|----------------|
| Message Storage | List of `Message` objects with metadata |
| Topic Tracking | `current_topic`, `topic_stack` |
| Entity Tracking | `current_entities`, `last_response_entities` |
| Reference Resolution | `resolve_references()` method |
| Context Summary | `get_context_summary()` for LLM |

#### Reference Resolution

```python
def resolve_references(query: str) -> Tuple[str, List[str]]:
    """
    "Who wrote it?" after discussing API docs
        → ("Who wrote it? (regarding: API Documentation)", ['API Documentation', 'Marcus Thompson'])
    """
```

#### Follow-up Context

The bot tracks entities mentioned in its own responses:

```python
def _extract_entities_from_response(response: str) -> List[str]:
    # Extract person names mentioned
    # Extract ticket IDs mentioned
    # Store in last_response_entities for follow-ups
```

---

### 5. Hallucination Prevention

#### Anti-Hallucination Rules

```python
CRITICAL RULES:
1. ONLY answer based on the provided context - DO NOT make up information
2. If the context mentions a person name, ticket ID, or fact, you can repeat it
3. NEVER invent commit SHAs, ticket IDs, dates, or names not in the context
4. For follow-up questions, look in context AND "MY LAST RESPONSE" section
5. If you mentioned something in your last response and user asks about it, reference that
```

#### No-Info Response

When no documents are found:

```python
def _generate_no_info_response(query, intent_type, entities):
    return "I don't have detailed information about {entities} in my current data."
```

---

## Data Flow

### Example: Multi-Turn Person Query

**Turn 1:** "What has Marcus been working on?"

```
1. Intent: person_query, entities=['Marcus Thompson']
2. Retrieve: Commits, tickets, decisions for Marcus
3. Create: Person summary document
4. LLM: Generates summary of Marcus's work
5. History: Store query + response + entities ['Marcus Thompson']
```

**Turn 2:** "Show me his recent commits"

```
1. Resolve: "his" → Marcus Thompson (from history)
2. Intent: person_query, entities=['Marcus Thompson']
3. Retrieve: Marcus's commits
4. LLM: Lists commits
5. History: Update with new response
```

**Turn 3:** "What decisions was he involved in?"

```
1. Resolve: "he" → Marcus Thompson
2. Intent: person_query (decision-focused)
3. Retrieve: Decisions where Marcus is in decided_by
4. LLM: Lists decisions
```

---

## Intent Types

| Intent | Trigger Keywords | Example Queries |
|--------|------------------|-----------------|
| `DECISION_QUERY` | why, decision, chose, rationale | "Why did we choose React?" |
| `PERSON_QUERY` | who, worked, Marcus, Lisa, frontend | "What has Marcus been working on?" |
| `TIMELINE_QUERY` | when, timeline, sprint, history | "What happened in Sprint 1?" |
| `HOWTO_QUERY` | how, setup, configure, install | "How do I set up the project?" |
| `STATUS_QUERY` | status, progress, done, blocked | "What's the status of Sprint 2?" |
| `TICKET_QUERY` | ONBOARD-XX, ticket, issue | "Tell me about ONBOARD-14" |
| `MEETING_QUERY` | meeting, discussed, planning | "What was discussed in planning?" |
| `SPRINT_SUMMARY_QUERY` | summary of sprint, sprint overview | "Give me a summary of Sprint 1" |
| `GENERAL_QUERY` | (fallback) | "Tell me about the project" |

---

## Retrieval Methods

### SQL Query Patterns

| Query Type | SQL Pattern |
|------------|-------------|
| Decision by topic | `WHERE title ILIKE '%react%' OR rationale ILIKE '%react%'` |
| Person commits | `WHERE author_name ILIKE '%Marcus%'` |
| Person tickets | `WHERE assignee ILIKE '%Marcus%' OR reporter ILIKE '%Marcus%'` |
| Sprint tickets | `JOIN sprint_tickets WHERE sprint_id = X` |
| Sprint decisions | `WHERE decision_date BETWEEN start AND end` |
| All Confluence | `SELECT * FROM confluence_pages` |

### Document Format

```python
@dataclass
class Document:
    content: str              # Main text
    title: str                # Title/summary
    source_type: str          # 'decision', 'commit', 'person_summary', etc.
    source_id: str            # UUID
    source_table: str         # Database table
    date: Optional[date]
    related_tickets: List[str]
    related_people: List[str]
    relevance_score: float
    metadata: Dict[str, Any]
```

---

## Conversation Features

### Reference Patterns Supported

| Pattern | Example | Resolution |
|---------|---------|------------|
| Pronouns | "Who made it?" | Uses current topic |
| Demonstratives | "that decision" | Uses current topic |
| Follow-ups | "What alternatives?" | Adds current topic as entity |
| Possessives | "his commits" | Uses last person mentioned |
| Author queries | "who wrote it?" | Uses last response entities |

### Topic Tracking

```python
class ConversationHistory:
    current_topic: str        # "React", "ONBOARD-14", etc.
    current_entities: List    # ["react", "frontend"]
    topic_stack: List         # History of topics discussed
    last_response_entities: List  # Entities mentioned in last response
```

---

## Configuration

### Environment Variables

```bash
# In database/.env
DATABASE_URL=postgresql://user:pass@host:port/db

# Or individual settings
DB_NAME=project_knowledge
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host.render.com
DB_PORT=5432

# Bytez API Key
BYTEZ_API_KEY=your_api_key_here
```

### Chatbot Settings

```python
# In main.py
MAX_HISTORY_TURNS = 10      # Keep last 10 exchanges
MAX_CONTEXT_CHARS = 8000    # Limit context for LLM
```

---

## Testing

### Run Interactive Mode

```bash
cd ~/Desktop/Onboarding_AI/chatbot
python main.py
```

### Run Tests

```bash
cd ~/Desktop/Onboarding_AI
python test_conversational.py --interactive
```

### Test Specific Features

```python
# Test person queries
bot = OnboardingChatbot(verbose=True)
bot.chat("What has Marcus been working on?")
bot.chat("Who worked on the frontend?")

# Test topic tracking
bot.chat("Why did we choose React?")
bot.chat("Who made that decision?")  # Should know "that" = React

# Test list queries
bot.chat("What Confluence pages are available?")
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: django` | Venv not activated | `source venv/bin/activate` |
| Person query returns empty | Name not recognized | Check `KNOWN_PERSONS` in retriever |
| "I don't have that information" | No documents retrieved | Check database has data |
| Topic command shows wrong topic | Context drift | Clear history and retry |
| Follow-up fails | Entities not tracked | Check `last_response_entities` |

### Debug Mode

```bash
# Enable verbose logging
bot = OnboardingChatbot(verbose=True)

# Or in CLI
👤 You: debug
🔧 Debug: ON
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Jan 2026 | Initial release - Single-turn Q&A |
| 2.0.0 | Jan 2026 | Conversational - Multi-turn with memory |
| 3.0.0 | Jan 2026 | Enhanced person queries, list support, hallucination prevention |

### v3.0.0 Changes

- ✅ Fixed `topic` CLI command
- ✅ Improved person query detection (names, roles, possessives)
- ✅ Added role-to-person mapping (frontend → Lisa Park)
- ✅ Added list query support (list all Confluence pages)
- ✅ Fixed follow-up context (tracks entities from responses)
- ✅ Added hallucination prevention
- ✅ Person summary documents
- ✅ Sprint status shows completion percentage

---

## Database Schema Reference

### Tables Used

| Table | Fields | Purpose |
|-------|--------|---------|
| `decisions` | title, rationale, alternatives, decided_by | Decision queries |
| `meetings` | title, summary, key_decisions, action_items | Meeting queries |
| `jira_tickets` | issue_key, summary, status, assignee | Ticket/status queries |
| `confluence_pages` | title, content, author | Documentation queries |
| `git_commits` | sha, message, author_name | Code/person queries |
| `sprints` | sprint_number, name, start_date, end_date | Sprint queries |
| `sprint_tickets` | sprint_id, ticket_id | Sprint-ticket mapping |
| `employees` | name, email, role | Team info |

---

## Author

Onboarding AI Project Team - Employee Onboarding Portal