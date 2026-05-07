# Decision Extraction System

## Overview

The Decision Extraction System automatically extracts, deduplicates, and stores architectural and technical decisions from multiple data sources. It creates a unified **Decision Timeline** that helps new team members understand not just *what* was built, but *why* those choices were made.

---

## Table of Contents

1. [The Problem](#the-problem)
2. [The Solution](#the-solution)
3. [Architecture](#architecture)
4. [Data Sources](#data-sources)
5. [Decision Table Schema](#decision-table-schema)
6. [DSPy-Style Implementation](#dspy-style-implementation)
7. [Deduplication Logic](#deduplication-logic)
8. [Setup Guide](#setup-guide)
9. [Usage](#usage)
10. [Example Output](#example-output)
11. [Decision vs Non-Decision](#decision-vs-non-decision)
12. [API Reference](#api-reference)

---

## The Problem

When onboarding new developers, they often ask:

> *"Why did we choose React over Vue?"*  
> *"Why are we using JWT instead of sessions?"*  
> *"When did we switch from Material UI to Tailwind?"*

This information is scattered across:
- Meeting recordings/transcripts
- Confluence documentation
- Jira ticket comments
- Git commit messages

**The challenge:** Decisions are buried in conversations, not explicitly documented.

---

## The Solution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DECISION EXTRACTION PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   DATA SOURCES                                                               │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│   │ Meetings │  │Confluence│  │   Jira   │  │  Commits │                   │
│   │  (WHY)   │  │  (WHAT)  │  │  (WHAT)  │  │  (WHAT)  │                   │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
│        │             │             │             │                          │
│        └─────────────┴─────────────┴─────────────┘                          │
│                              │                                               │
│                              ▼                                               │
│        ┌─────────────────────────────────────────────────┐                  │
│        │            LLM EXTRACTION (Bytez API)           │                  │
│        │                                                 │                  │
│        │  DSPy-Style Components:                         │                  │
│        │  • Signatures (typed I/O contracts)             │                  │
│        │  • ChainOfThought (step-by-step reasoning)      │                  │
│        │  • Refined prompts (exclude task completions)   │                  │
│        └─────────────────────┬───────────────────────────┘                  │
│                              │                                               │
│                              ▼                                               │
│        ┌─────────────────────────────────────────────────┐                  │
│        │              DEDUPLICATION                       │                  │
│        │                                                 │                  │
│        │  • Title similarity matching (SequenceMatcher)  │                  │
│        │  • Links duplicates via related_decisions       │                  │
│        │  • Configurable threshold (default: 0.70)       │                  │
│        └─────────────────────┬───────────────────────────┘                  │
│                              │                                               │
│                              ▼                                               │
│        ┌─────────────────────────────────────────────────┐                  │
│        │              DECISIONS TABLE                     │                  │
│        │                                                 │                  │
│        │  Unified timeline with:                         │                  │
│        │  • What was decided                             │                  │
│        │  • Why (rationale)                              │                  │
│        │  • Who decided                                  │                  │
│        │  • When                                         │                  │
│        │  • Related tickets & decisions                  │                  │
│        └─────────────────────────────────────────────────┘                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture

### What Each Source Provides

| Source | Provides | Example |
|--------|----------|---------|
| **Meetings** | The **WHY** - reasoning, discussions, trade-offs | "We chose JWT because it's stateless and scales better" |
| **Confluence** | The **WHAT** - documented decisions, final choices | "Authentication: JWT tokens" |
| **Jira** | The **WHAT** - decisions in ticket discussions | "Switched to Tailwind per team discussion" |
| **Git Commits** | The **WHAT** - implementation decisions | "refactor: switch from Material UI to Tailwind" |

### Processing Order (Priority)

```
1. MEETINGS (Primary)     → Contains reasoning and context
2. CONFLUENCE (Secondary) → Documents decisions from meetings  
3. JIRA (Tertiary)        → Decisions in ticket discussions
```

Meetings are processed first so that Confluence/Jira duplicates can be linked back to the original decision.

---

## Data Sources

### Meetings → Decisions

```
Meeting Transcript:
┌────────────────────────────────────────────────────────────┐
│ Sarah: "I think we should use JWT for authentication"      │
│ Marcus: "Agreed, it's stateless and works better for APIs" │
│ Sarah: "Let's go with JWT then"                            │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    Decision     │
                    ├─────────────────┤
                    │ Title: Use JWT  │
                    │ Rationale:      │
                    │ Stateless,      │
                    │ better for APIs │
                    │ Decided by:     │
                    │ Sarah, Marcus   │
                    └─────────────────┘
```

### Confluence → Decisions

```
Confluence Page: "Technical Architecture"
┌────────────────────────────────────────────────────────────┐
│ ## Authentication                                          │
│ We use JWT tokens for authentication.                      │
│                                                            │
│ **Why:** Stateless, scalable, works well with React SPA    │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    Decision     │
                    │    [DUPLICATE]  │
                    ├─────────────────┤
                    │ Title: Use JWT  │
                    │ Related to:     │
                    │ Meeting decision│
                    └─────────────────┘
```

### Jira → Decisions

```
ONBOARD-16 Comments:
┌────────────────────────────────────────────────────────────┐
│ Lisa: "Material UI is too heavy, switching to Tailwind"    │
│ Sarah: "Approved, Tailwind gives us more flexibility"      │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    Decision     │
                    ├─────────────────┤
                    │ Title: Switch   │
                    │ to Tailwind     │
                    │ Related ticket: │
                    │ ONBOARD-16      │
                    └─────────────────┘
```

---

## Decision Table Schema

```sql
CREATE TABLE decisions (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core Decision Info
    title VARCHAR(500) NOT NULL,           -- What was decided
    description TEXT,                       -- Detailed description
    decision_date DATE NOT NULL,           -- When decided
    
    -- Context and Reasoning (THE "WHY")
    rationale TEXT,                         -- Why this was decided
    alternatives_considered TEXT,           -- Other options discussed
    impact TEXT,                            -- What this affects
    
    -- People
    decided_by VARCHAR(255)[],              -- Who participated
    
    -- Source Tracking
    source_type VARCHAR(50) NOT NULL,       -- meeting, confluence, jira
    source_id UUID,                         -- Link to source record
    source_title VARCHAR(500),              -- Source name for display
    
    -- Relationships
    related_tickets VARCHAR(50)[],          -- ['ONBOARD-11', 'ONBOARD-12']
    related_decisions UUID[],               -- Links to duplicate/related decisions
    
    -- Categorization
    category VARCHAR(100),                  -- architecture, technology, process, etc.
    tags TEXT[],                            -- Flexible tagging
    
    -- Lifecycle
    status VARCHAR(50) DEFAULT 'active',    -- active, superseded, reversed
    superseded_by UUID,                     -- If this decision was replaced
    supersedes UUID,                        -- If this replaces another decision
    
    -- Metadata
    confidence_score FLOAT,                 -- LLM confidence (0-1)
    extraction_notes TEXT,                  -- Notes from extraction
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Field Descriptions

| Field | Purpose | Example |
|-------|---------|---------|
| `title` | Short description of what was decided | "Use React for frontend" |
| `rationale` | **WHY** - the reasoning behind the choice | "Component-based, team has experience" |
| `alternatives_considered` | Other options that were discussed | "Vue, Angular, Svelte" |
| `decided_by` | People who participated in the decision | ["Sarah Chen", "Marcus Thompson"] |
| `source_type` | Where the decision was found | "meeting" |
| `source_title` | Name of the source | "Sprint 1 Planning" |
| `related_tickets` | Jira tickets related to this decision | ["ONBOARD-11", "ONBOARD-15"] |
| `related_decisions` | UUIDs of duplicate/related decisions | [uuid1, uuid2] |
| `category` | Type of decision | "technology" |
| `status` | Current state | "active" or "superseded" |
| `superseded_by` | If replaced, link to new decision | UUID of new decision |
| `confidence_score` | How confident the LLM was | 0.9 |

---

## DSPy-Style Implementation

### What is DSPy?

DSPy is a framework for programming LLMs in a structured, modular way. Instead of brittle prompt strings, you define:

1. **Signatures** - Input/output contracts
2. **Modules** - Reusable components
3. **ChainOfThought** - Step-by-step reasoning

### Our Implementation

```python
# ============================================
# 1. SIGNATURES (Define I/O Contract)
# ============================================

class ExtractDecisionsFromMeeting(Signature):
    """Extract DECISIONS (not tasks) from a meeting."""
    
    # Inputs
    transcript = InputField(desc="Meeting transcript")
    meeting_title = InputField(desc="Title of the meeting")
    participants = InputField(desc="Meeting participants")
    
    # Outputs
    decisions = OutputField(desc="JSON array of decisions")


# ============================================
# 2. CHAIN OF THOUGHT (Step-by-step reasoning)
# ============================================

class ChainOfThought:
    """Adds reasoning steps before extraction."""
    
    def _build_prompt(self, **kwargs):
        return """
        Think step by step:
        1. Read through the content carefully
        2. Look for statements where a CHOICE was made
        3. For each choice, extract WHY it was made
        4. SKIP task completions and status updates
        5. Categorize each decision
        """


# ============================================
# 3. LLM BACKEND (Bytez API)
# ============================================

class BytezLM:
    """Wrapper for Bytez API - DSPy-style interface."""
    
    def generate(self, prompt: str) -> str:
        results = self.model.run([{
            "role": "user", 
            "content": prompt
        }])
        return results.output


# ============================================
# 4. EXTRACTOR MODULE (Composable Pipeline)
# ============================================

class DecisionExtractor:
    """Composes multiple extractors into a pipeline."""
    
    def __init__(self, lm, deduplicator):
        self.meeting_extractor = ChainOfThought(ExtractDecisionsFromMeeting)
        self.confluence_extractor = ChainOfThought(ExtractDecisionsFromConfluence)
        self.jira_extractor = ChainOfThought(ExtractDecisionsFromJira)
```

### Why DSPy-Style?

| Traditional Prompts | DSPy-Style |
|---------------------|------------|
| Hardcoded strings | Declarative signatures |
| Brittle, hard to modify | Modular, composable |
| No type safety | Typed inputs/outputs |
| Manual parsing | Automatic structured output |

---

## Deduplication Logic

### The Problem

The same decision appears in multiple sources:

```
Meeting:    "We decided to use JWT for authentication"
Confluence: "Authentication: JWT tokens"
Jira:       "Implemented JWT auth as discussed"
```

### The Solution

```python
class DecisionDeduplicator:
    """Finds and links duplicate decisions."""
    
    def __init__(self, similarity_threshold=0.70):
        self.similarity_threshold = similarity_threshold
    
    def normalize_title(self, title):
        """Remove common prefixes for comparison."""
        # "Use React" and "Adopt React" → "react"
        prefixes = ['use ', 'adopt ', 'implement ', 'choose ']
        for prefix in prefixes:
            if title.lower().startswith(prefix):
                title = title[len(prefix):]
        return title.lower().strip()
    
    def calculate_similarity(self, title1, title2):
        """Compare two titles using SequenceMatcher."""
        t1 = self.normalize_title(title1)
        t2 = self.normalize_title(title2)
        return SequenceMatcher(None, t1, t2).ratio()
    
    def is_duplicate(self, new_title):
        """Check if decision already exists."""
        for existing_id, existing_title in self.existing_decisions:
            if self.calculate_similarity(new_title, existing_title) >= 0.70:
                return (True, [existing_id])
        return (False, [])
```

### Example

```
Existing:  "Use JWT for authentication"
New:       "JWT for authentication"

Normalized existing: "jwt for authentication"
Normalized new:      "jwt for authentication"

Similarity: 1.0 → DUPLICATE DETECTED

Action: Link new decision to existing via related_decisions field
```

---

## Setup Guide

### Step 1: Create the Database Table

```sql
-- Run in psql
\i sql/002_create_decisions_table.sql
```

Or manually:

```sql
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    decision_date DATE NOT NULL,
    rationale TEXT,
    alternatives_considered TEXT,
    impact TEXT,
    decided_by VARCHAR(255)[],
    source_type VARCHAR(50) NOT NULL,
    source_id UUID,
    source_title VARCHAR(500),
    related_tickets VARCHAR(50)[],
    related_decisions UUID[],
    category VARCHAR(100),
    tags TEXT[],
    status VARCHAR(50) DEFAULT 'active',
    superseded_by UUID REFERENCES decisions(id),
    supersedes UUID REFERENCES decisions(id),
    confidence_score FLOAT,
    extraction_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decisions_date ON decisions(decision_date);
CREATE INDEX idx_decisions_source ON decisions(source_type, source_id);
CREATE INDEX idx_decisions_status ON decisions(status);
CREATE INDEX idx_decisions_category ON decisions(category);
```

### Step 2: Add Django Model

Add to `knowledge_base/models.py`:

```python
class Decision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    decision_date = models.DateField()
    rationale = models.TextField(blank=True, null=True)
    alternatives_considered = models.TextField(blank=True, null=True)
    impact = models.TextField(blank=True, null=True)
    decided_by = ArrayField(models.CharField(max_length=255), blank=True, null=True)
    source_type = models.CharField(max_length=50)
    source_id = models.UUIDField(blank=True, null=True)
    source_title = models.CharField(max_length=500, blank=True, null=True)
    related_tickets = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    related_decisions = ArrayField(models.UUIDField(), blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    tags = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    status = models.CharField(max_length=50, default='active')
    superseded_by = models.ForeignKey('self', null=True, blank=True, 
                                       on_delete=models.SET_NULL,
                                       related_name='supersedes_decisions',
                                       db_column='superseded_by')
    supersedes = models.ForeignKey('self', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='superseded_by_decisions',
                                    db_column='supersedes')
    confidence_score = models.FloatField(blank=True, null=True)
    extraction_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'decisions'
        managed = False
        ordering = ['-decision_date']
```

### Step 3: Add Admin Registration

Add to `knowledge_base/admin.py`:

```python
@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ['decision_date', 'title', 'category', 'source_type', 'status']
    list_filter = ['status', 'category', 'source_type', 'decision_date']
    search_fields = ['title', 'description', 'rationale']
    ordering = ['-decision_date']
```

### Step 4: Set Environment Variable

Add to `.env`:

```bash
BYTEZ_API_KEY=your-api-key-here
```

---

## Usage

### Basic Commands

```bash
# See available options
python scripts/extract_decisions.py --help

# Dry run (preview without saving)
python scripts/extract_decisions.py --all --dry-run

# Extract from all sources
python scripts/extract_decisions.py --all

# Extract from specific source
python scripts/extract_decisions.py --meetings
python scripts/extract_decisions.py --confluence
python scripts/extract_decisions.py --jira

# Skip duplicate decisions
python scripts/extract_decisions.py --all --skip-duplicates

# Clear and re-extract
python scripts/extract_decisions.py --all --clear

# Adjust similarity threshold
python scripts/extract_decisions.py --all --similarity 0.80

# Use different model
python scripts/extract_decisions.py --all --model openai/gpt-4o-mini
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--all` | Process all sources | - |
| `--meetings` | Process meetings only | - |
| `--confluence` | Process Confluence only | - |
| `--jira` | Process Jira only | - |
| `--dry-run` | Preview without saving | False |
| `--clear` | Clear existing decisions first | False |
| `--skip-duplicates` | Don't save duplicate decisions | False |
| `--similarity` | Similarity threshold for dedup | 0.70 |
| `--model` | Bytez model to use | openai/gpt-4o |

---

## Example Output

```
============================================================
DSPy-Style Decision Extractor with Bytez Backend
============================================================

Settings:
  API Key: 1940871681...
  Model: openai/gpt-4o
  Similarity Threshold: 0.7
  Skip Duplicates: True

============================================================
PROCESSING MEETINGS (Primary source)
============================================================
Found 5 meetings

→ Sprint1 Meeting1 Planning
  Extracted 6 decisions
    • Use Django for backend
    • Use React for frontend
    • Use PostgreSQL for database
    • Use JWT for authentication
    • Use AWS for deployment
    • Use GitHub Actions for CI/CD

→ Sprint1 Meeting2 Midsprint
  Extracted 4 decisions
    • Switch from Material UI to Tailwind CSS
    • Use ECS Fargate for container deployment
    • Simplify employee API for this sprint
    • Implement basic role-based access

============================================================
PROCESSING CONFLUENCE (Secondary source)
============================================================

→ Technical Architecture
  Extracted 4 decisions
    • Use Tailwind for Styling [DUP]
    • Use JWT for Authentication [DUP]
    • Add SQLAlchemy for Complex Queries
    • Use ECS Fargate for Deployment [DUP]

============================================================
COMPLETE
============================================================
  Total found:      28
  Duplicates:       12
  Saved:            16
  Skipped:          12
```

---

## Decision vs Non-Decision

### ✅ These ARE Decisions (Extract)

| Example | Why It's a Decision |
|---------|---------------------|
| "We decided to use React instead of Vue" | Choice between alternatives |
| "We chose JWT over session-based auth" | Choice with reasoning |
| "We will switch from Material UI to Tailwind" | Change in direction |
| "Managers will see all employees, not just direct reports" | Design choice |
| "We'll use PostgreSQL for the database" | Technology choice |

### ❌ These are NOT Decisions (Skip)

| Example | Why It's NOT a Decision |
|---------|-------------------------|
| "Login page is done" | Task completion |
| "Marcus will set up the project" | Action item/assignment |
| "Tests are passing" | Status update |
| "I'll have it ready by Friday" | Commitment/deadline |
| "PR is up for review" | Status update |
| "Fixed the bug in authentication" | Bug fix |
| "Added unit tests" | Task completion |

---

## API Reference

### DecisionExtractor

```python
extractor = DecisionExtractor(lm=BytezLM(), deduplicator=DecisionDeduplicator())

# Extract from meeting
decisions = extractor.extract_from_meeting(meeting)

# Extract from Confluence
decisions = extractor.extract_from_confluence(page)

# Extract from Jira
decisions = extractor.extract_from_jira(ticket)
```

### DecisionDeduplicator

```python
deduplicator = DecisionDeduplicator(similarity_threshold=0.70)

# Load existing decisions
deduplicator.load_existing_decisions()

# Check if duplicate
is_dup, related_ids = deduplicator.is_duplicate("Use JWT for auth")

# Add new decision to tracker
deduplicator.add_decision(uuid, "Use JWT for auth", "meeting")
```

### BytezLM

```python
lm = BytezLM(model_name="openai/gpt-4o")

# Generate response
response = lm.generate("Extract decisions from this text...")
```

---

## Common Queries

### View Decision Timeline

```sql
SELECT decision_date, title, category, source_type, rationale
FROM decisions
WHERE status = 'active'
ORDER BY decision_date ASC;
```

### Find Decisions by Category

```sql
SELECT title, rationale, decided_by
FROM decisions
WHERE category = 'technology'
ORDER BY decision_date DESC;
```

### Find Related Decisions

```sql
SELECT d1.title as decision, d2.title as related_to
FROM decisions d1
CROSS JOIN LATERAL unnest(d1.related_decisions) as rd(id)
JOIN decisions d2 ON d2.id = rd.id;
```

### Find Superseded Decisions

```sql
SELECT 
    old.title as old_decision,
    old.decision_date as old_date,
    new.title as new_decision,
    new.decision_date as new_date
FROM decisions old
JOIN decisions new ON old.superseded_by = new.id;
```

### Django Shell Queries

```python
from knowledge_base.models import Decision

# All active decisions
Decision.objects.filter(status='active').order_by('decision_date')

# Technology decisions
Decision.objects.filter(category='technology')

# Decisions from meetings
Decision.objects.filter(source_type='meeting')

# Decisions with high confidence
Decision.objects.filter(confidence_score__gte=0.9)
```

---

## Troubleshooting

### "Decision() got unexpected keyword arguments"

Your Django model is missing fields. Ensure all fields from the schema are in the model.

### "column does not exist"

Run the SQL schema to add missing columns:

```sql
ALTER TABLE decisions ADD COLUMN related_decisions UUID[];
```

### No decisions extracted

1. Check if source data exists (meetings, confluence, jira)
2. Verify Bytez API key is valid
3. Run with `--dry-run` to see extraction results

### Too many duplicates

Increase similarity threshold:

```bash
python scripts/extract_decisions.py --all --similarity 0.85
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `sql/002_create_decisions_table.sql` | Database schema |
| `models_decision_complete.py` | Django model |
| `scripts/extract_decisions.py` | Extraction script |
| `docs/DECISIONS.md` | This documentation |

---

*Last updated: February 2026*