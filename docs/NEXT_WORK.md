# LIGHTHOUSE — Status & Next Work

> Last updated: 2026-05-06  
> Branch: `decision-intelligence`  
> Author: Kousik / LIGHTHOUSE team  
> Resume from: any machine with the repo cloned and venv activated

---

## Everything Built: Status

| # | Work item | Status | Key files |
|---|---|---|---|
| 1 | Semantic deduplication (MiniLM embeddings) | **Done** | `extract_decisions.py` → `DecisionDeduplicator` |
| 2 | Drift detection (`drift_risk`, `last_reinforced_at`) | **Done** | `check_drift.py`, `models.py` |
| 3 | Groq LLM backend migration | **Done** | `extract_decisions.py`, `summarize_meetings.py` |
| 4 | LLM conflict detection | **Done** | `check_conflicts.py`, `migrate_add_conflicts_table.sql` |
| 5 | Provenance chain traversal | **Done** | `provenance.py` |
| 6 | Chatbot wired to conflicts + provenance | **Done** | `chatbot/` — all 6 files updated |

---

## Current DB State

```
Decisions in DB   : 44
Active            : 43
Superseded        : 1
Conflicts detected: 2  (1 high, 1 medium)
Meetings summarized: 5 / 5

Supersession chain:
  "Use Material UI for components" → "Switch to Tailwind CSS"

Conflicts:
  [HIGH]   Use GitHub Actions instead of Jenkins  ↔  Use AWS for deployment
  [MEDIUM] Simplify Employee API for This Sprint  ↔  Show all employees to managers
```

---

## Chatbot — What the New Intents Handle

Two new intents were added. Users can now ask:

**Conflict queries** (intent: `conflict_query`):
- "Are there any conflicting decisions?"
- "Does SQLAlchemy conflict with anything?"
- "Show me architectural conflicts"
- "What decisions contradict each other?"

**Provenance queries** (intent: `provenance_query`):
- "Where did the JWT decision come from?"
- "Trace the Tailwind CSS decision"
- "Show me the history behind SQLAlchemy"
- "What commits followed the JWT decision?"

Both intents are detected before general keyword scoring. The retrieval is pure SQL — no LLM call needed for the data fetch, only for narration. If the Groq rate limit is hit, the raw structured data still reaches the user.

---

## What's Left to Do

### Priority 1: Run `check_drift.py` — populate drift fields

The `last_reinforced_at` and `drift_risk` fields exist in the DB but have never been computed against the current 44 decisions. This is a one-command job:

```bash
cd /Users/Masters/Projects/Onboarding_AI/database
/Users/Masters/Projects/Onboarding_AI/venv/bin/python3.12 scripts/check_drift.py
```

Then run `--report` to see results. This produces a strong demo moment — showing decisions that are high-drift (technology not mentioned in any recent commit or ticket) versus low-drift (actively referenced). Ask the chatbot "what is the drift risk of the ECS Fargate decision?" after running it.

---

### Priority 2: Merge `decision-intelligence` → `main`

All work is stable and pushed. When ready to present:

```bash
git checkout main
git merge decision-intelligence
git push origin main
```

Check for conflicts with the `chatbot` branch first:
```bash
git diff main..chatbot --stat
```

---

### Priority 3 (optional): One-command demo script

A single script that tells the full story end-to-end would be compelling on stage:

```bash
python scripts/demo.py
# 1. Shows 44 decisions in the timeline
# 2. Runs check_drift   → shows high/medium/low risk decisions
# 3. Runs check_conflicts --report → shows 2 conflicts
# 4. Runs provenance on JWT → shows origin meeting + 17 commits
```

Each step maps to one of the 5 changes. 30 seconds, no terminal switching.

---

## How to Resume

### 1. Activate the environment
```bash
cd /Users/Masters/Projects/Onboarding_AI
/Users/Masters/Projects/Onboarding_AI/venv/bin/python3.12 --version   # 3.12.x
```
> **Note:** The venv `pip` shebang is broken (old path). Always use `venv/bin/python3.12 -m pip` instead of `venv/bin/pip`.

### 2. Check the branch
```bash
git checkout decision-intelligence
git pull origin decision-intelligence
```

### 3. Verify DB is alive
```bash
cd database
/Users/Masters/Projects/Onboarding_AI/venv/bin/python3.12 -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from knowledge_base.models import Decision, DecisionConflict
print('Decisions:', Decision.objects.count())
print('Conflicts:', DecisionConflict.objects.count())
"
```
Expected: `Decisions: 44  Conflicts: 2`

### 4. Run the chatbot
```bash
cd /Users/Masters/Projects/Onboarding_AI
/Users/Masters/Projects/Onboarding_AI/venv/bin/python3.12 chatbot/main.py
```

Try these questions to demo the new intents:
```
Are there any conflicting decisions?
Where did the JWT decision come from?
Trace the Tailwind CSS decision
Does SQLAlchemy conflict with anything?
```

### 5. Useful one-liners
```bash
# Run drift check (populates drift_risk fields)
python3.12 scripts/check_drift.py
python3.12 scripts/check_drift.py --report

# Run conflict report
python3.12 scripts/check_conflicts.py --report

# Trace a decision's provenance (CLI, no LLM needed)
python3.12 scripts/provenance.py --decision "JWT"
python3.12 scripts/provenance.py --decision "Tailwind"
python3.12 scripts/provenance.py --all

# Re-extract decisions (if DB was reset) — wait for Groq limit to reset first
python3.12 scripts/extract_decisions.py --meetings --confluence
python3.12 scripts/summarize_meetings.py --all
```

### 6. If the Render DB is suspended (>90 days inactive)
Create a new Render PostgreSQL instance, update `database/.env`, then re-run the full ingest:
```bash
python3.12 scripts/ingest_all.py
python3.12 scripts/summarize_meetings.py --all
python3.12 scripts/extract_decisions.py --all
python3.12 scripts/check_conflicts.py
python3.12 scripts/check_drift.py
```

---

## Key Files Reference

| File | Purpose |
|---|---|
| `database/.env` | All credentials (Render DB, Groq API key, Jira, Confluence) |
| `database/config/settings.py` | Django settings, DB connection (SSL required for Render) |
| `database/knowledge_base/models.py` | All ORM models — Decision, DecisionConflict, Meeting, EntityReference, etc. |
| `database/scripts/extract_decisions.py` | Decision extraction pipeline (LLM + dedup + supersession) |
| `database/scripts/summarize_meetings.py` | Meeting summarizer |
| `database/scripts/check_drift.py` | Drift risk scoring — **run this before demo** |
| `database/scripts/check_conflicts.py` | LLM conflict detection |
| `database/scripts/provenance.py` | Provenance chain CLI |
| `chatbot/main.py` | Chatbot entry point |
| `chatbot/llm/bytez_llm.py` | Groq LLM wrapper (renamed BytezLLM for compatibility) |
| `chatbot/intent/types.py` | All intent types incl. CONFLICT_QUERY, PROVENANCE_QUERY |
| `chatbot/retriever/sql_retriever.py` | All retrieval methods incl. conflicts + provenance |
| `docs/DECISION_INTELLIGENCE_CHANGES.md` | Full technical changelog — read before presenting |
| `LIGHTHOUSE_Pitch_Guide.docx` | Pitch deck guide |

---

## Important Constraints

- **Render DB free tier** — suspends after 90 days of inactivity. Keep it warm or upgrade before the presentation.
- **Groq free tier** — 100k tokens/day, resets midnight UTC. The chatbot's conflict and provenance intents only use the LLM for narration — the retrieval itself is pure SQL and always works even when rate-limited.
- **sentence-transformers** — MiniLM model (~80MB) downloads on first use. Run `check_conflicts.py` once before the demo to warm the cache.
- **`managed = False` on all Django models** — tables are created by raw SQL migration files, not `python manage.py migrate`.

---

## Scoring Estimate

| Dimension | Estimated score | What delivers it |
|---|---|---|
| Innovation | 9/10 | Conflict detection is genuinely novel; chatbot answers "what contradicts what?" |
| Technical depth | 9/10 | Embeddings + LLM judgement + relational graph traversal + conversational interface |
| Feasibility | 9/10 | Live DB, all scripts working, chatbot answering new question types |
| Impact | 9/10 | Drift + conflicts + provenance + chatbot together cover every question a new hire has |
| Presentation | TBD | Use on-stage phrases from `DECISION_INTELLIGENCE_CHANGES.md` — one per change |
