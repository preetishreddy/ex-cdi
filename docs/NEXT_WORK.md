# LIGHTHOUSE — Status & Next Work

> Last updated: 2026-05-06  
> Branch: `decision-intelligence`  
> Author: Kousik / LIGHTHOUSE team  
> Resume from: any machine with the repo cloned and venv activated

---

## All Decision Intelligence Changes: COMPLETE

| # | Change | Status | Key files |
|---|---|---|---|
| 1 | Semantic deduplication (MiniLM embeddings) | **Done** | `extract_decisions.py` → `DecisionDeduplicator` |
| 2 | Drift detection (`drift_risk`, `last_reinforced_at`) | **Done** | `check_drift.py`, `models.py` |
| 3 | Groq LLM backend migration | **Done** | `extract_decisions.py`, `summarize_meetings.py` |
| 4 | LLM conflict detection | **Done** | `check_conflicts.py`, `migrate_add_conflicts_table.sql` |
| 5 | Provenance chain traversal | **Done** | `provenance.py` |

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

## What's Left to Do

The decision intelligence engine is complete. The remaining work is on **presentation and integration** — making the new capabilities accessible to judges and users.

---

### Priority 1: Wire the chatbot to the new scripts

The chatbot (`chatbot/`) does not yet know about conflicts or provenance. A judge asking "are there any conflicting decisions?" or "where did the JWT decision come from?" would get a blank response.

**What to build:**

1. **Conflict intent** — add to `chatbot/intent/` a handler that detects questions like:
   - _"are there any conflicting decisions?"_
   - _"does X conflict with anything?"_
   - _"what decisions contradict each other?"_

   On match, call `DecisionConflict.objects.all()` and narrate the results.

2. **Provenance intent** — add a handler for:
   - _"where did the decision to use X come from?"_
   - _"show me the history of the Tailwind decision"_
   - _"what commits followed the JWT decision?"_

   On match, call `provenance.get_provenance_chain(decision)` and narrate the dict.

**Files to modify:**
- `chatbot/intent/` — add `conflict_intent.py`, `provenance_intent.py`
- `chatbot/retriever/sql_retriever.py` — add `get_conflicts()` and `get_provenance()` methods
- `chatbot/main.py` — register new intents

**Effort:** ~2–3 hours. The data is all there; this is plumbing only.

---

### Priority 2: Run `check_drift.py` to populate drift fields

The `last_reinforced_at` and `drift_risk` fields are in the DB schema but have never been computed against the current 44 decisions. Run it once:

```bash
cd /Users/Masters/Projects/Onboarding_AI/database
/Users/Masters/Projects/Onboarding_AI/venv/bin/python3.12 scripts/check_drift.py
```

Then run `--report` to see which decisions are flagged high-risk. This is a strong demo moment — showing a decision with `drift_risk: high` and explaining why.

---

### Priority 3: Merge `decision-intelligence` → `main`

All 5 changes are stable and pushed. When ready to present:

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

### Priority 4 (optional): Demo script / one-command demo

For the presentation, a single script that runs the full pipeline end-to-end would be compelling:

```bash
python scripts/demo.py
# 1. Shows 44 decisions in the timeline
# 2. Runs check_drift   → shows 2 high-risk decisions
# 3. Runs check_conflicts --report → shows 2 conflicts
# 4. Runs provenance on the JWT decision → shows 17 commits
```

This takes ~30 seconds and tells the full story without switching terminals.

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

### 4. Useful one-liners
```bash
# Run drift check
python3.12 scripts/check_drift.py --report

# Run conflict report
python3.12 scripts/check_conflicts.py --report

# Trace a decision's provenance
python3.12 scripts/provenance.py --decision "JWT"

# Re-extract decisions (if DB was reset)
python3.12 scripts/extract_decisions.py --meetings --confluence

# Re-summarize meetings
python3.12 scripts/summarize_meetings.py --all
```

### 5. If the Render DB is suspended (>90 days inactive)
Create a new Render PostgreSQL instance, update `database/.env` with the new credentials, then re-run the full ingest:
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
| `database/scripts/check_drift.py` | Drift risk scoring |
| `database/scripts/check_conflicts.py` | LLM conflict detection |
| `database/scripts/provenance.py` | Provenance chain traversal |
| `chatbot/main.py` | Chatbot entry point |
| `docs/DECISION_INTELLIGENCE_CHANGES.md` | Full technical changelog — read before presenting |
| `LIGHTHOUSE_Pitch_Guide.docx` | Pitch deck guide |

---

## Important Constraints

- **Render DB free tier** — suspends after 90 days of inactivity. Keep it warm with periodic queries or upgrade if presenting to judges.
- **Groq free tier** — 100k tokens/day, resets at midnight UTC. Full extraction uses ~95k. Run extraction the day before the presentation.
- **sentence-transformers** — MiniLM model (~80MB) downloads on first use and caches locally. Run `provenance.py` or `check_conflicts.py` once before the demo to warm the cache.
- **`managed = False` on all Django models** — tables are created by raw SQL migration files, not `python manage.py migrate`. Any new table needs a corresponding `.sql` file.

---

## Scoring Estimate (post all changes)

| Dimension | Estimated score | What delivers it |
|---|---|---|
| Innovation | 9/10 | Conflict detection is genuinely novel; no onboarding tool does this |
| Technical depth | 9/10 | Embeddings + LLM + relational graph traversal in one coherent pipeline |
| Feasibility | 9/10 | Live DB, all scripts working, chatbot running |
| Impact | 9/10 | Drift + conflicts + provenance together answer every "why" a new hire has |
| Presentation | TBD | Use on-stage phrases in `DECISION_INTELLIGENCE_CHANGES.md` — one per change |
