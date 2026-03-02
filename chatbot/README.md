# Onboarding AI Chatbot - Technical Documentation

> **Version 2.0.0** - Conversational Chatbot with Memory

This document provides a detailed explanation of each file and component in the chatbot system.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Folder Structure](#folder-structure)
4. [Core Components](#core-components)
   - [Conversation History](#1-conversation-history)
   - [Intent Classification](#2-intent-classification)
   - [SQL Retrieval](#3-sql-retrieval)
   - [Context Building](#4-context-building)
   - [LLM Integration](#5-llm-integration)
5. [File-by-File Documentation](#file-by-file-documentation)
6. [Data Flow](#data-flow)
7. [Conversation Features](#conversation-features)
8. [Database Schema Reference](#database-schema-reference)
9. [Future Enhancements](#future-enhancements)

---

## Overview

The Onboarding AI Chatbot is a **conversational assistant** that helps team members understand the Employee Onboarding Portal project. Unlike simple Q&A bots, it maintains conversation history and can handle follow-up questions.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-turn Conversations** | Remembers previous messages in a session |
| **Reference Resolution** | Understands "it", "that", "they" from context |
| **Intent Classification** | Categorizes queries into 8 types |
| **Database Retrieval** | Fetches from PostgreSQL (decisions, meetings, tickets, etc.) |
| **Context-Aware Responses** | GPT-4o generates answers based on retrieved data |

### What It Can Answer

- **Decisions**: "Why did we choose React?" → "Who made that decision?"
- **People**: "What has Marcus been working on?" → "Show me his commits"
- **Tickets**: "Tell me about ONBOARD-14" → "What's its status?"
- **Meetings**: "What was discussed in Sprint 1 Planning?"
- **Setup**: "How do I set up the project locally?"
- **Timeline**: "What happened in Sprint 1?"

---

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER QUERY                                      │
│                "Who made that decision?" (referring to React)                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     0. CONVERSATION HISTORY                                  │
│                                                                              │
│   • Check previous messages for context                                     │
│   • Resolve "that decision" → "React decision"                              │
│   • Carry forward entities from recent turns                                │
│                                                                              │
│   Previous: "Why did we choose React?" → entities: ['react']                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         1. INTENT CLASSIFIER                                 │
│                            (intent/)                                         │
│                                                                              │
│   • Classifies query type (decision_query, person_query, etc.)              │
│   • Extracts new entities                                                    │
│   • Combines with entities from conversation history                        │
│                                                                              │
│   Output: IntentType.DECISION_QUERY, confidence=0.85                        │
│           entities=['react'] (from history)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          2. SQL RETRIEVER                                    │
│                            (retriever/)                                      │
│                                                                              │
│   • Routes to appropriate database tables based on intent                   │
│   • Executes Django ORM queries                                             │
│   • Fetches related data (commits, meetings, tickets)                       │
│                                                                              │
│   Query: SELECT * FROM decisions WHERE title ILIKE '%react%'                │
│   Output: [Document(decision: "Use React for frontend"), ...]               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         3. CONTEXT BUILDER                                   │
│                            (context/)                                        │
│                                                                              │
│   • Formats documents into structured context                               │
│   • Adds conversation history summary                                       │
│   • Applies intent-specific prompt templates                                │
│                                                                              │
│   Output: Formatted prompt with history + context + query                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            4. LLM (Bytez)                                    │
│                              (llm/)                                          │
│                                                                              │
│   • Sends prompt to GPT-4o via Bytez API                                    │
│   • Extracts response                                                       │
│                                                                              │
│   Output: "The React decision was made by Sarah Chen and Marcus Thompson    │
│            during the Sprint 1 Planning meeting..."                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         5. UPDATE HISTORY                                    │
│                                                                              │
│   • Store user query + assistant response                                   │
│   • Update current entities and topic                                       │
│   • Trim old messages if exceeding limit                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RESPONSE                                        │
│                                                                              │
│   ChatResponse(                                                              │
│       answer="The React decision was made by Sarah Chen...",                │
│       intent="decision_query",                                              │
│       confidence=0.85,                                                      │
│       sources=["decision:Use React for frontend"],                          │
│       entities=["react"],                                                   │
│       conversation_turn=2                                                   │
│   )                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
chatbot/
├── __init__.py              # Package exports (v2.0.0)
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
│   └── sql_retriever.py     # PostgreSQL retrieval (Phase 1)
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

### 1. Conversation History

**Location:** `main.py` → `ConversationHistory` class

The conversation history system enables multi-turn conversations by:

#### Message Storage
```python
@dataclass
class Message:
    role: str           # 'user' or 'assistant'
    content: str        # The message text
    timestamp: datetime # When it was sent
    intent: str         # Classified intent (for user messages)
    entities: List[str] # Extracted entities
```

#### Key Methods

| Method | Purpose |
|--------|---------|
| `add_user_message()` | Store user query with intent and entities |
| `add_assistant_message()` | Store bot response |
| `get_context_summary()` | Get last 3 exchanges for LLM context |
| `get_recent_entities()` | Get entities from recent turns |
| `resolve_references()` | Convert "it"/"that" to actual entities |
| `clear()` | Reset conversation |

#### Reference Resolution

```python
# User's previous query: "Why did we choose React?"
# Extracted entity: ['react']

# Current query: "Who made that decision?"
# After resolution: "Who made that decision? (referring to: react)"
```

#### Configuration

```python
MAX_HISTORY_TURNS = 10  # Keep last 10 exchanges (20 messages)
```

---

### 2. Intent Classification

**Location:** `intent/` folder

#### Intent Types

| Intent | Trigger Keywords | Target Tables |
|--------|------------------|---------------|
| `DECISION_QUERY` | why, decision, chose, switch, rationale | decisions, meetings |
| `PERSON_QUERY` | who, worked, assigned, responsible | employees, jira_tickets, git_commits |
| `TIMELINE_QUERY` | when, timeline, sprint, history | decisions, sprints, meetings |
| `HOWTO_QUERY` | how, setup, configure, install | confluence_pages |
| `STATUS_QUERY` | status, progress, done, open, blocked | jira_tickets |
| `TICKET_QUERY` | ONBOARD-XX, ticket, issue, jira | jira_tickets, git_commits |
| `MEETING_QUERY` | meeting, discussed, planning, standup | meetings |
| `GENERAL_QUERY` | (fallback) | all tables |

#### Entity Extraction

The classifier extracts:

| Entity Type | Pattern | Example |
|-------------|---------|---------|
| Ticket IDs | `ONBOARD-\d+` | ONBOARD-14 |
| Person Names | Predefined list | Sarah Chen, Marcus |
| Sprint Numbers | `Sprint\s*\d+` | Sprint 1 |
| Tech Terms | Keyword list | react, django, jwt |

#### Classification Flow

```
Query: "Who worked on authentication?"
         │
         ▼
    Extract Entities → ['authentication']
         │
         ▼
    Score Each Intent:
      - person_query: 2 (who, worked)
      - decision_query: 0
      - ...
         │
         ▼
    Select Highest → person_query
         │
         ▼
    Calculate Confidence → 0.75
         │
         ▼
    Return ClassifiedIntent(
        intent_type=PERSON_QUERY,
        confidence=0.75,
        entities=['authentication']
    )
```

---

### 3. SQL Retrieval

**Location:** `retriever/` folder

#### Approach: Structured Context Injection

Unlike traditional RAG (vector search), we use **direct SQL queries** because:

1. Our data is already well-structured (decisions have rationale, relationships)
2. Small dataset (~100 records) - no need for embeddings
3. Explicit relationships via `entity_references` table
4. Faster and cheaper than vector search

#### Query Routing

```python
def retrieve(self, query, intent_type, entities, limit):
    routing = {
        'decision_query': self._retrieve_decisions,
        'person_query': self._retrieve_person_info,
        'timeline_query': self._retrieve_timeline,
        'howto_query': self._retrieve_documentation,
        'status_query': self._retrieve_status,
        'ticket_query': self._retrieve_ticket_info,
        'meeting_query': self._retrieve_meetings,
        'general_query': self._retrieve_general,
    }
    return routing[intent_type](query, entities, limit)
```

#### Document Format

All retrieved data is converted to a universal `Document` format:

```python
@dataclass
class Document:
    content: str              # Main text
    title: str                # Title/summary
    source_type: str          # 'decision', 'meeting', 'jira', etc.
    source_id: str            # UUID
    source_table: str         # Database table
    date: Optional[date]      # Relevant date
    related_tickets: List[str]
    related_people: List[str]
    relevance_score: float    # 0-1
    metadata: Dict[str, Any]  # Extra fields
```

---

### 4. Context Building

**Location:** `context/` folder

#### Context Formatting

Each document type is formatted differently:

```
📋 DECISION: Use React for frontend
Date: 2026-01-06
Category: technology
Status: active
Decided by: Sarah Chen, Marcus Thompson
Related tickets: ONBOARD-13

Description: React chosen for component-based architecture
Rationale: Team expertise, community support
Alternatives Considered: Vue, Angular
```

```
🎫 TICKET: ONBOARD-14: Implement JWT authentication
Status: Done
Type: Story
Priority: High
Assignee: Marcus Thompson
Sprint: Sprint 1

Description: Implement JWT-based authentication...
```

#### History Integration

For conversational context, history is prepended:

```
CONVERSATION HISTORY:
User: Why did we choose React?
Assistant: React was chosen because of team expertise...

User: Who made that decision?

---

RELEVANT INFORMATION FROM DATABASE:
📋 DECISION: Use React for frontend
...
```

#### Token Management

```python
MAX_CONTEXT_CHARS = 8000   # Document context limit
MAX_HISTORY_CHARS = 1500   # Conversation history limit
```

---

### 5. LLM Integration

**Location:** `llm/` folder

#### Bytez API Wrapper

```python
class BytezLLM:
    DEFAULT_MODEL = "openai/gpt-4o"
    
    def generate(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        results = self.model.run(messages)
        return self._extract_response(results.output)
```

#### Prompt Structure

```
You are an AI assistant for the Employee Onboarding Portal project.
You are having a CONVERSATION with a team member.

INSTRUCTIONS: [Intent-specific instructions]

IMPORTANT RULES:
1. Only answer based on the provided context
2. If user refers to "it", "that", use conversation history
3. Cite your sources
4. If you don't know, say so
5. Be concise but complete

CONTEXT:
[Conversation history + Retrieved documents]

CURRENT QUESTION: [User's query]

Provide a helpful answer:
```

---

## File-by-File Documentation

### `main.py`

**Purpose:** Main orchestrator that ties all components together.

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `Message` | Single message in conversation |
| `ConversationHistory` | Manages multi-turn memory |
| `ChatResponse` | Structured response with metadata |
| `OnboardingChatbot` | Main chatbot class |

**Key Methods:**

```python
class OnboardingChatbot:
    def chat(query) -> ChatResponse      # Full pipeline with history
    def chat_simple(query) -> str        # Just the answer
    def clear_history()                   # Reset conversation
    def get_conversation_length() -> int  # Number of turns
    def health_check() -> dict            # Component status
```

**CLI Commands:**
- `python main.py` - Interactive mode
- `python main.py --test` - Run tests
- Type `clear` - Clear history
- Type `debug` - Toggle verbose mode
- Type `help` - Show examples
- Type `quit` - Exit

---

### `django_setup.py`

**Purpose:** Configures Django to access PostgreSQL from outside the Django project.

**What it does:**
1. Adds `database/` folder to Python path
2. Loads `.env` file for database credentials
3. Initializes Django settings
4. Provides `get_models()` function

```python
from django_setup import get_models

models = get_models()
Decision = models['Decision']
Meeting = models['Meeting']
# ...
```

---

### `intent/types.py`

**Purpose:** Defines all intent types and their configurations.

**Key Components:**

```python
class IntentType(Enum):
    DECISION_QUERY = "decision_query"
    PERSON_QUERY = "person_query"
    # ... 8 total types

@dataclass
class IntentConfig:
    intent_type: IntentType
    keywords: List[str]      # Trigger words
    tables: List[str]        # Target tables
    description: str
    example_queries: List[str]

@dataclass
class ClassifiedIntent:
    intent_type: IntentType
    confidence: float        # 0-1
    entities: List[str]      # Extracted entities
    original_query: str
```

---

### `intent/classifier.py`

**Purpose:** Classifies user queries into intent types.

**Algorithm:**
1. Extract entities (ticket IDs, names, tech terms)
2. Check for direct ticket reference → TICKET_QUERY
3. Score each intent by keyword matches
4. Select highest scoring intent
5. Calculate confidence
6. Return ClassifiedIntent

**Entity Patterns:**
```python
PATTERNS = {
    'ticket_id': r'\b(ONBOARD-\d+)\b',
    'person_name': r'\b(Sarah Chen|Marcus Thompson|...)\b',
    'sprint': r'\b[Ss]print\s*(\d+)\b',
}
```

---

### `retriever/base.py`

**Purpose:** Defines abstract interface for all retrievers.

**Key Classes:**

```python
class Document:
    """Universal format for retrieved data"""
    content: str
    title: str
    source_type: str
    # ...

class BaseRetriever(ABC):
    """Interface for Phase 2/3 swapping"""
    @abstractmethod
    def retrieve(query, intent_type, entities, limit) -> List[Document]
    
    @abstractmethod
    def retrieve_by_id(source_type, source_id) -> Optional[Document]
```

---

### `retriever/sql_retriever.py`

**Purpose:** Phase 1 implementation - direct PostgreSQL queries.

**Retrieval Methods:**

| Method | Tables | Use Case |
|--------|--------|----------|
| `_retrieve_decisions()` | decisions | Why questions |
| `_retrieve_person_info()` | commits, tickets, decisions | Who questions |
| `_retrieve_timeline()` | decisions, sprints | When questions |
| `_retrieve_documentation()` | confluence_pages | How-to questions |
| `_retrieve_status()` | jira_tickets | Status questions |
| `_retrieve_ticket_info()` | tickets, commits, decisions | Ticket details |
| `_retrieve_meetings()` | meetings | Meeting info |
| `_retrieve_general()` | all | Fallback |

**Document Converters:**
- `_decision_to_document()`
- `_meeting_to_document()`
- `_ticket_to_document()`
- `_confluence_to_document()`
- `_commit_to_document()`

---

### `context/templates.py`

**Purpose:** System prompts and intent-specific templates.

**Templates:**
- `SYSTEM_PROMPT` - Base instructions
- `CONVERSATIONAL_SYSTEM_PROMPT` - Multi-turn instructions
- `PromptTemplates.decision_query()` - Decision-focused
- `PromptTemplates.person_query()` - Person-focused
- ... (one per intent type)

---

### `context/builder.py`

**Purpose:** Transforms documents into LLM-ready context.

**Key Methods:**

```python
class ContextBuilder:
    def build_context(documents, intent_type) -> str
    def build_context_with_history(documents, intent_type, history) -> str
    def build_prompt(documents, intent_type, query) -> str
    def build_conversational_prompt(documents, intent_type, query, history) -> str
```

**Document Formatters:**
- `_format_decision()` - 📋 emoji, rationale, alternatives
- `_format_meeting()` - 🗓️ emoji, participants, summary
- `_format_ticket()` - 🎫 emoji, status, assignee
- `_format_confluence()` - 📄 emoji, author, content
- `_format_commit()` - 💻 emoji, SHA, author

---

### `llm/bytez_llm.py`

**Purpose:** Wrapper for Bytez API (GPT-4o access).

**Configuration:**
```python
BytezLLM(
    model_name="openai/gpt-4o",
    api_key=None,        # From env or hardcoded
    max_tokens=2000,
    temperature=0.7
)
```

**Methods:**
```python
def generate(prompt) -> str           # Basic generation
def generate_with_context(query, context, intent) -> str
def health_check() -> dict            # Verify working
```

---

## Data Flow

### Example: Multi-Turn Conversation

**Turn 1:** "Why did we choose React?"

```
1. History: Empty
2. Intent: decision_query, entities=['react']
3. Retrieve: Decision "Use React for frontend"
4. Context: [Decision document]
5. LLM: "React was chosen because..."
6. Update History: Store query + response + entities
```

**Turn 2:** "Who made that decision?"

```
1. History: Contains Turn 1
2. Resolve: "that decision" → "react" (from history entities)
3. Intent: decision_query, entities=['react'] (from history)
4. Retrieve: Same decision document
5. Context: [History summary] + [Decision document]
6. LLM: "The decision was made by Sarah Chen and Marcus Thompson..."
7. Update History: Store query + response
```

**Turn 3:** "What alternatives were considered?"

```
1. History: Contains Turn 1 + Turn 2
2. Intent: decision_query, entities=['react'] (carried over)
3. Retrieve: Decision with alternatives
4. Context: [History summary] + [Decision document]
5. LLM: "Vue and Angular were considered as alternatives..."
6. Update History: Store query + response
```

---

## Conversation Features

### Reference Resolution

| User Says | Resolved To |
|-----------|-------------|
| "Tell me more about it" | "Tell me more about [last entity]" |
| "Who made that decision?" | "Who made that decision? (referring to: react)" |
| "What's its status?" | "What's its status? (referring to: ONBOARD-14)" |

### Topic Continuity

Entities are carried forward for 6 messages (3 turns):

```python
def get_recent_entities(self) -> List[str]:
    entities = set()
    for msg in self.messages[-6:]:  # Last 3 exchanges
        entities.update(msg.entities)
    return list(entities)
```

### History Limits

| Limit | Value | Purpose |
|-------|-------|---------|
| `MAX_HISTORY_TURNS` | 10 | Prevent token overflow |
| `MAX_HISTORY_CHARS` | 1500 | Limit history in prompt |
| `MAX_CONTEXT_CHARS` | 8000 | Limit document context |

---

## Database Schema Reference

### Tables Used

| Table | Fields Used | Purpose |
|-------|-------------|---------|
| `decisions` | title, description, rationale, alternatives_considered, impact, decided_by, status, supersedes | Decision queries |
| `meetings` | title, meeting_date, summary, key_decisions, action_items, participants | Meeting queries |
| `jira_tickets` | issue_key, summary, description, status, assignee, reporter, comments, sprint | Ticket queries |
| `confluence_pages` | title, content, author, labels | Documentation queries |
| `git_commits` | sha, message, author_name, commit_date, related_tickets | Code queries |
| `employees` | name, email, role, department | Person queries |

### Key Relationships

```
decisions.supersedes → decisions.id (decision history)
decisions.related_tickets → jira_tickets.issue_key
git_commits.related_tickets → jira_tickets.issue_key
entity_references → links all sources to tickets
```

---

## Future Enhancements

### Phase 2: Add PGVector (Hybrid Search)

```python
class HybridRetriever(BaseRetriever):
    def __init__(self):
        self.sql_retriever = SQLRetriever()  # Reuse!
        self.embedding_model = OpenAIEmbeddings()
    
    def retrieve(self, query, intent_type, entities, limit):
        sql_results = self.sql_retriever.retrieve(...)
        
        if intent_type in ['general_query', 'howto_query']:
            vector_results = self._semantic_search(query)
            return self._merge_and_rerank(sql_results, vector_results)
        
        return sql_results
```

### Phase 3: Full RAG

- Dedicated vector database (Pinecone/Weaviate)
- Document chunking with overlap
- Reranking with Cohere
- Larger document corpus

### Planned Improvements

1. **Better Intent Classification**
   - LLM-based classification for ambiguous queries
   - Custom NER for domain-specific entities

2. **Enhanced Retrieval**
   - Semantic search for unstructured content
   - Cross-table relationship traversal

3. **Conversation Features**
   - Persistent sessions (database-backed)
   - User preferences and context

4. **Response Quality**
   - Source citations with links
   - Confidence indicators
   - "I don't know" handling

---

## Testing

### Run Module Tests

```bash
cd ~/Desktop/Onboarding_AI/chatbot

# Test individual modules
python -m intent.classifier
python -m retriever.sql_retriever
python -m context.builder
python -m llm.bytez_llm
```

### Run Integration Test

```bash
python main.py --test
```

### Run Conversational Test

```bash
cd ~/Desktop/Onboarding_AI
python test_conversational.py
python test_conversational.py --interactive
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: django` | Activate venv: `source venv/bin/activate` |
| `ModuleNotFoundError: django_setup` | Run from `chatbot/` directory |
| Database connection error | Check `database/.env` file |
| LLM not responding | Verify Bytez API key |
| Wrong intent classification | Check keywords in `intent/types.py` |
| Missing results | Verify data exists in database |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Jan 2026 | Initial release - Single-turn Q&A |
| 2.0.0 | Jan 2026 | Conversational - Multi-turn with memory |

---

## Author

Onboarding AI Project Team
## Transition Summary
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TRANSITION ROADMAP                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 1 (Now)                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ IntentClassifier + SQLRetriever + ContextBuilder + BytezLLM         │   │
│  │                                                                     │   │
│  │ • Build intent classifier                                           │   │
│  │ • Build SQL queries for each intent                                 │   │
│  │ • Build context templates                                           │   │
│  │ • Build chatbot interface                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  │ ADD: PGVector + Embeddings               │
│                                  │ KEEP: Everything else                    │
│                                  ▼                                          │
│  PHASE 2 (When needed)                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ IntentClassifier + HybridRetriever + ContextBuilder + BytezLLM      │   │
│  │                     ▲                                               │   │
│  │                     │                                               │   │
│  │         ┌───────────┴───────────┐                                   │   │
│  │         │                       │                                   │   │
│  │    SQLRetriever           PGVectorSearch                            │   │
│  │    (reused!)              (new)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                          │
│                                  │ ADD: Pinecone + Reranker                 │
│                                  │ KEEP: SQL for structured queries         │
│                                  ▼                                          │
│  PHASE 3 (If needed)                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ IntentClassifier + RAGRetriever + ContextBuilder + BytezLLM         │   │
│  │                     ▲                                               │   │
│  │                     │                                               │   │
│  │         ┌───────────┴───────────┐                                   │   │
│  │         │                       │                                   │   │
│  │    SQLRetriever           PineconeSearch + Reranker                 │   │
│  │    (still reused!)        (new)                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘