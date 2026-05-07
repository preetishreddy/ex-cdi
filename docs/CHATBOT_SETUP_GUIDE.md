# Onboarding AI Chatbot - Setup & User Guide

> **Version 3.0.0** - Conversational Chatbot with Enhanced Features

This guide covers setup, usage, and integration of the Onboarding AI Chatbot.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Running the Chatbot](#running-the-chatbot)
5. [Features & Capabilities](#features--capabilities)
6. [Example Conversations](#example-conversations)
7. [CLI Commands](#cli-commands)
8. [API Integration](#api-integration)
9. [Supported Query Types](#supported-query-types)
10. [Troubleshooting](#troubleshooting)
11. [Architecture Overview](#architecture-overview)

---

## Overview

The Onboarding AI Chatbot helps team members understand the Employee Onboarding Portal project through natural conversation. It can answer questions about decisions, people, tickets, meetings, and more.

### What It Can Do

| Capability | Example |
|------------|---------|
| **Decision Queries** | "Why did we choose React?" → "Who made that decision?" |
| **Person Tracking** | "What has Marcus been working on?" |
| **Role-Based Lookups** | "Who worked on the frontend?" → Lisa Park |
| **Sprint Summaries** | "Give me a summary of Sprint 1" |
| **Ticket Details** | "Tell me about ONBOARD-14" → "What commits are related?" |
| **Documentation** | "How do I set up the development environment?" |
| **Meeting Summaries** | "What was discussed in Sprint 1 Planning?" |
| **List Queries** | "What Confluence pages are available?" |

### Key Features (v3.0)

- ✅ Multi-turn conversations with memory
- ✅ Reference resolution ("it", "that", "who wrote it")
- ✅ Role-to-person mapping (frontend → Lisa Park)
- ✅ Person work summaries (commits, tickets, decisions)
- ✅ List all resources queries
- ✅ Sprint status with completion percentage
- ✅ Hallucination prevention (won't make up information)

---

## Quick Start

```bash
# 1. Navigate to project
cd ~/Desktop/Onboarding_AI

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run the chatbot
cd chatbot
python main.py
```

---

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL database (populated with project data)
- Virtual environment with dependencies

### Step-by-Step Setup

```bash
# 1. Clone repository (if needed)
git clone <repository-url>
cd Onboarding_AI

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify database connection
cd database
python manage.py shell
>>> from knowledge_base.models import Decision
>>> Decision.objects.count()
# Should return a number > 0

# 5. Run the chatbot
cd ../chatbot
python main.py
```

### Environment Configuration

Ensure `database/.env` contains:

```bash
DATABASE_URL=postgresql://username:password@host:port/database_name
# Or individual settings:
DB_NAME=project_knowledge
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host.render.com
DB_PORT=5432

# Optional: Bytez API Key (has default fallback)
BYTEZ_API_KEY=your_api_key
```

---

## Running the Chatbot

### Interactive CLI Mode

```bash
cd ~/Desktop/Onboarding_AI/chatbot
python main.py
```

You'll see:

```
============================================================
🤖 ONBOARDING AI CHATBOT (Conversational v3)
============================================================

Welcome! I remember our conversation.

Commands:
  'quit'   - Exit
  'help'   - Example questions
  'clear'  - Clear history
  'debug'  - Toggle debug mode
  'topic'  - Show current topic
  'status' - Show bot status

👤 You (turn 1): 
```

### Test Mode

```bash
cd ~/Desktop/Onboarding_AI
python test_conversational.py --interactive
```

### Programmatic Usage

```python
from chatbot import OnboardingChatbot

# Initialize
bot = OnboardingChatbot(verbose=False)

# Simple query
answer = bot.chat_simple("Why did we choose React?")
print(answer)

# Full response with metadata
response = bot.chat("Why did we choose React?")
print(f"Answer: {response.answer}")
print(f"Intent: {response.intent}")
print(f"Sources: {response.sources}")

# Follow-up (bot remembers context)
response = bot.chat("Who made that decision?")
print(response.answer)  # Knows "that" refers to React

# Clear history
bot.clear_history()
```

---

## Features & Capabilities

### 1. Multi-Turn Conversations

The chatbot remembers your conversation:

```
👤 You: Why did we choose React?
🤖 Bot: React was chosen for its component-based architecture...

👤 You: Who made that decision?
🤖 Bot: Sarah Chen and Lisa Park made the React decision...

👤 You: What alternatives were considered?
🤖 Bot: Vue and Angular were considered as alternatives...
```

### 2. Person Queries

Find information about team members:

```
👤 You: What has Marcus been working on?
🤖 Bot: Marcus Thompson has been working on:
        - Commits: JWT authentication, user model
        - Tickets: ONBOARD-14, ONBOARD-17
        - Decisions: PostgreSQL, SQLAlchemy integration

👤 You: Show me his commits
🤖 Bot: Marcus's recent commits:
        - feat: implement JWT authentication endpoints
        - feat: add user model with role field
        ...
```

### 3. Role-Based Lookups

Ask about roles, get person names:

```
👤 You: Who worked on the frontend?
🤖 Bot: Lisa Park worked on the frontend. She created:
        - Login page UI component
        - Dashboard layout
        - Employee list view

👤 You: Who should I contact about backend?
🤖 Bot: For backend questions, contact Marcus Thompson.
```

**Role Mappings:**

| Role | Person(s) |
|------|-----------|
| Frontend, UI, React | Lisa Park |
| Backend, API, Auth | Marcus Thompson |
| Database, Schema | Sarah Chen, Marcus Thompson |
| DevOps, CI/CD | Dave Rossi |

### 4. Sprint Summaries

Get comprehensive sprint overviews:

```
👤 You: Give me a summary of Sprint 1
🤖 Bot: SPRINT 1: Foundation (Jan 5-16, 2026)

        STATISTICS:
        - Total Tickets: 10
        - Completed: 8
        - Decisions Made: 12
        - Contributors: 7

        KEY DECISIONS:
        - Use Django for backend
        - Use React for frontend
        - Use PostgreSQL for database
        ...

👤 You: What's the status of Sprint 2?
🤖 Bot: SPRINT 2 STATUS: ✅ COMPLETED
        Progress: 10/10 tickets (100%)
        🎉 All Sprint 2 tickets completed!
```

### 5. List Queries

List all available resources:

```
👤 You: What Confluence pages are available?
🤖 Bot: Found 6 Confluence pages:
        - Employee Onboarding Portal - Project Overview
        - Local Development Setup Guide
        - Technical Architecture
        - API Documentation
        - Database Schema Documentation
        - Testing Strategy

👤 You: List all decisions
🤖 Bot: Found 15 active decisions:
        - Use React for frontend
        - Use Django for backend
        - Use PostgreSQL for database
        ...
```

### 6. Follow-Up Context

The bot tracks what it mentioned:

```
👤 You: Summarize the API documentation
🤖 Bot: The API documentation covers endpoints for auth, 
        employees, and tasks. It was authored by Marcus Thompson...

👤 You: Who wrote it?
🤖 Bot: The API documentation was written by Marcus Thompson.
```

---

## Example Conversations

### Flow 1: Decision Deep-Dive

```
👤 You: Why did we choose React?
🤖 Bot: React was chosen for its component-based architecture, 
        which allows building reusable UI elements...

👤 You: Who made that decision?
🤖 Bot: The decision was made by Sarah Chen and Lisa Park...

👤 You: What alternatives were considered?
🤖 Bot: Vue and Angular were considered as alternatives...
```

### Flow 2: Person Investigation

```
👤 You: What has Marcus been working on?
🤖 Bot: Marcus Thompson has worked on:
        - JWT authentication implementation
        - User model with role field
        - Employee CRUD API
        ...

👤 You: Show me his commits
🤖 Bot: Marcus's commits:
        - feat: implement JWT authentication endpoints (a8b9c0d1)
        - feat: add user model with role field (f7a8b9c0)
        ...

👤 You: What decisions was he involved in?
🤖 Bot: Marcus was involved in:
        - Use PostgreSQL for database
        - Add SQLAlchemy Core for complex queries
        ...
```

### Flow 3: Sprint Analysis

```
👤 You: What's the summary of Sprint 1?
🤖 Bot: [Comprehensive summary with stats, tickets, decisions]

👤 You: What about Sprint 2?
🤖 Bot: [Sprint 2 summary - all tickets completed]

👤 You: Who contributed most?
🤖 Bot: The main contributors were Marcus Thompson, Lisa Park, 
        and Sarah Chen...
```

### Flow 4: Onboarding Help

```
👤 You: I just joined the team. What should I know?
🤖 Bot: Here's an overview of the project...

👤 You: How do I set up locally?
🤖 Bot: [Step-by-step setup guide]

👤 You: Who should I contact for questions?
🤖 Bot: For frontend: Lisa Park
        For backend: Marcus Thompson
        For database: Sarah Chen
        For DevOps: Dave Rossi
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `quit` | Exit the chatbot |
| `help` | Show example questions |
| `clear` | Clear conversation history (start fresh) |
| `debug` | Toggle debug mode (shows detailed logs) |
| `topic` | Show current conversation topic and entities |
| `status` | Show bot health status |

### Using Topic Command

```
👤 You: Why did we choose React?
🤖 Bot: React was chosen because...

👤 You: topic
📌 Current topic: react
📌 Current entities: ['react', 'frontend']
📌 Conversation turns: 1
```

---

## API Integration

### Flask Integration

```python
from flask import Flask, request, jsonify
from chatbot import OnboardingChatbot

app = Flask(__name__)
bots = {}

def get_bot(session_id):
    if session_id not in bots:
        bots[session_id] = OnboardingChatbot()
    return bots[session_id]

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get('session_id', 'default')
    query = data.get('query', '')
    
    bot = get_bot(session_id)
    response = bot.chat(query)
    
    return jsonify({
        'answer': response.answer,
        'intent': response.intent,
        'sources': response.sources,
        'turn': response.conversation_turn
    })

@app.route('/api/clear', methods=['POST'])
def clear():
    session_id = request.json.get('session_id', 'default')
    if session_id in bots:
        bots[session_id].clear_history()
    return jsonify({'status': 'cleared'})
```

### FastAPI Integration

```python
from fastapi import FastAPI
from chatbot import OnboardingChatbot

app = FastAPI()
sessions = {}

@app.post("/chat")
async def chat(query: str, session_id: str = "default"):
    if session_id not in sessions:
        sessions[session_id] = OnboardingChatbot()
    
    bot = sessions[session_id]
    response = bot.chat(query)
    
    return {
        "answer": response.answer,
        "intent": response.intent,
        "sources": response.sources
    }
```

---

## Supported Query Types

| Query Type | Keywords | Example |
|------------|----------|---------|
| **Decisions** | why, decision, chose, rationale | "Why did we choose React?" |
| **People** | who, worked, Marcus, Lisa | "What has Marcus worked on?" |
| **Roles** | frontend, backend, devops | "Who worked on frontend?" |
| **Tickets** | ONBOARD-XX, ticket, issue | "Tell me about ONBOARD-14" |
| **Sprints** | sprint summary, sprint X | "Summary of Sprint 1" |
| **Status** | status, progress, blockers | "Sprint 2 status" |
| **Meetings** | meeting, discussed, planning | "Sprint 1 Planning meeting" |
| **Documentation** | how, setup, configure | "How to set up locally?" |
| **Lists** | list all, what pages, available | "What Confluence pages?" |

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: django` | Run `source venv/bin/activate` |
| "I don't have that information" | Check database has data, verify entities |
| Person query returns empty | Use full name or check spelling |
| Wrong intent detected | Try rephrasing the question |
| Follow-up doesn't work | Use `topic` command to check context |

### Debug Mode

Enable verbose logging:

```
👤 You: debug
🔧 Debug: ON

👤 You: What has Marcus been working on?
[Shows: Query resolution, Intent classification, Retrieved documents, Context building]
```

### Check Database

```bash
cd ~/Desktop/Onboarding_AI/database
python manage.py shell

>>> from knowledge_base.models import *
>>> Decision.objects.count()
>>> GitCommit.objects.filter(author_name__icontains='marcus').count()
>>> JiraTicket.objects.filter(assignee__icontains='lisa').count()
```

---

## Architecture Overview

```
User Query
    │
    ▼
┌───────────────────┐
│ Conversation      │ ← Resolve "it", "that", track topic
│ History           │
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ Intent            │ ← Classify: person_query, decision_query, etc.
│ Classifier        │ ← Extract entities: names, ticket IDs
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ SQL               │ ← Query PostgreSQL via Django ORM
│ Retriever         │ ← Create summary documents
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ Context           │ ← Format documents + history
│ Builder           │ ← Apply intent-specific templates
└───────────────────┘
    │
    ▼
┌───────────────────┐
│ LLM               │ ← GPT-4o via Bytez API
│ (Bytez)           │ ← Anti-hallucination rules
└───────────────────┘
    │
    ▼
Response to User
```

### Database Tables

| Table | Purpose |
|-------|---------|
| `decisions` | Project decisions with rationale |
| `meetings` | Meeting summaries and action items |
| `jira_tickets` | Tickets with status, assignee |
| `confluence_pages` | Documentation content |
| `git_commits` | Commit history by author |
| `sprints` | Sprint dates and goals |
| `sprint_tickets` | Sprint-ticket mapping |

---

## Version History

| Version | Changes |
|---------|---------|
| 1.0.0 | Single-turn Q&A |
| 2.0.0 | Multi-turn conversations |
| 3.0.0 | Person queries, role mapping, list queries, hallucination prevention |

---

## Support

For issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Run in debug mode
3. Verify database has data
4. Check `chatbot/README.md` for technical details

---

*Last updated: January 2026 - Version 3.0.0*