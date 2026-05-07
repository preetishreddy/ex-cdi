# Project Overview Page — Frontend Specification

**Version:** 1.0
**Last updated:** March 2026
**Scope:** Full spec for the Project Overview page including all sprint blocks, tabs, data sources, and AI-generated content.

---

## Table of Contents

1. [Page Overview](#1-page-overview)
2. [Global AI Confidence Standard](#2-global-ai-confidence-standard)
3. [Layer 1 — Project Header](#3-layer-1--project-header)
4. [Layer 2 — Sprint Cards Grid](#4-layer-2--sprint-cards-grid)
5. [Layer 3 — Sprint Block Header](#5-layer-3--sprint-block-header)
6. [Layer 4 — Tab 1: AI Sprint Summary](#6-layer-4--tab-1-ai-sprint-summary)
7. [Layer 5 — Tab 2: Meetings](#7-layer-5--tab-2-meetings)
8. [Layer 6 — Tab 3: Tickets](#8-layer-6--tab-3-tickets)
9. [Layer 7 — Tab 4: Decisions & Velocity](#9-layer-7--tab-4-decisions--velocity)
10. [Future Work Summary](#10-future-work-summary)
11. [Data Model Quick Reference](#11-data-model-quick-reference)

---

## 1. Page Overview

The Project Overview page is reached when a user clicks on a specific project from the projects list. It is the central hub for all project-related data — every sprint, meeting, ticket, commit, decision, and document tied to that project lives here.

### Page Flow

```
Projects List
     │
     ▼
Project Overview Page          ← you are here
     │
     ├── Project Header         (always visible)
     │
     ├── Sprint Cards Grid      (all sprints for this project)
     │
     └── Sprint Detail View     (on clicking a sprint card)
              │
              ├── Sprint Block Header   (always visible inside sprint)
              │
              └── Tabs
                   ├── Tab 1: AI Sprint Summary
                   ├── Tab 2: Meetings
                   ├── Tab 3: Tickets
                   └── Tab 4: Decisions & Velocity
```

### Data Sources

All data on this page is pulled from the following backend tables:

| Table | What it stores |
|---|---|
| `projects` | Project metadata |
| `sprints` | Sprint dates, goals, status |
| `sprint_tickets` | Links sprints to Jira tickets |
| `jira_tickets` | Ticket details, status, story points |
| `meetings` | Meeting transcripts, summaries, participants |
| `git_commits` | Commit metadata and messages |
| `git_commit_files` | Files changed per commit |
| `entity_references` | Cross-source links (commit ↔ ticket, meeting ↔ ticket) |
| `decisions` | Decisions extracted from all sources |
| `employees` | Team member profiles for name resolution |
| `confluence_pages` | Documentation pages |

---

## 2. Global AI Confidence Standard

Wherever AI generates or extracts content on this page, a confidence indicator is shown using a consistent visual pattern. This applies to:

- Sprint AI summary (Tab 1)
- Meeting summaries (Tab 2)
- Meeting key decisions (Tab 2)
- Meeting action items (Tab 2)
- Individual decisions (Tab 4)

### Visual Pattern

```
AI Generated  ·  Confidence: 84% ████████░░  ·  Generated Mar 1, 2026
```

### Confidence Thresholds

| Score | Bar colour | Behaviour |
|---|---|---|
| 80–100% | Green | No warning |
| 60–79% | Amber | Tooltip: "Review recommended" |
| 0–59% | Red | Tooltip: "Low confidence — verify against source" |

### Hover Tooltip

On hovering the confidence bar, show a breakdown of what reduced the score. Examples:

```
"Confidence reduced because:
 · Meeting transcript had unidentified speakers (SPEAKER_01)
 · Summary length is short relative to transcript length"
```

```
"Confidence reduced because:
 · Several tickets in this sprint have no description filled
 · 2 of 4 meetings have no AI summary yet"
```

### Fields Required Per Model

| Model | Field | Type | Status |
|---|---|---|---|
| `sprints` | `summary_confidence` | FloatField | Future work |
| `sprints` | `summary_generated_at` | DateTimeField | Future work |
| `sprints` | `summary_text` | TextField | Future work |
| `meetings` | `summary_confidence` | FloatField | Future work |
| `meetings` | `decisions_confidence` | FloatField | Future work |
| `meetings` | `action_items_confidence` | FloatField | Future work |
| `decisions` | `confidence_score` | FloatField | **Already exists** |

---

## 3. Layer 1 — Project Header

The topmost section of the page. Visible at all times. Gives the user full context about the project before they interact with any sprint.

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  [Active]  Payment Gateway                                      │
│  End-to-end payment processing system with reporting            │
│                                                                 │
│  Owner: Preet     GitHub: org/repo     Jira: PAY               │
│  Confluence: ONBOARD                                            │
│  Started: Jan 1, 2026   Target: Mar 31, 2026                   │
│  Tags: [payments] [backend] [api]                               │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐     │
│  │ 4 Sprints│  │ 67% Done │  │ 142 pts  │  │ 8 Decisions│     │
│  │          │  │          │  │ completed│  │            │     │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Direct Fields

| Display | Table | Column | Notes |
|---|---|---|---|
| Project name | `projects` | `name` | Page heading |
| Description | `projects` | `description` | Subtitle |
| Status badge | `projects` | `status` | `active` / `completed` / `on_hold` / `cancelled` |
| Owner | `projects` | `owner` | Plain text |
| GitHub link | `projects` | `github_repo` | Clickable external link |
| Jira project key | `projects` | `jira_project_key` | e.g. `PAY` |
| Confluence space | `projects` | `confluence_space_key` | e.g. `ONBOARD` |
| Start date | `projects` | `start_date` | |
| Target end date | `projects` | `target_end_date` | |
| Actual end date | `projects` | `actual_end_date` | Shown only if completed |
| Tags | `projects` | `tags` | Array field, render as chips |

### Derived Stats

| Stat | How to derive | Tables involved |
|---|---|---|
| Sprint count | `COUNT(*)` where `project_id = X` | `sprints` |
| Overall completion % | Closed tickets / total tickets across all sprints | `sprint_tickets` → `jira_tickets.status` |
| Total story points completed | `SUM(story_points)` where `status = 'Done'` across all sprints | `jira_tickets.story_points` |
| Total decisions | `COUNT(*)` where `decision_date` falls within any sprint of this project | `decisions` |

### Additional Derived Features

- **Last activity indicator** — `MAX(commit_date)` from `git_commits` linked to this project via entity references. Display as "Last commit: 2 days ago."
- **Active sprint callout** — query `sprints` where `status = 'active'` and `project_id = X`. Show a highlighted banner: "Sprint 4 is active."
- **At risk signal** — if active sprint has >30% open tickets and is past 70% of its duration, show a subtle "At risk" badge next to project status.

### Future Work

| Missing | Impact |
|---|---|
| `actual_end_date` population | Show "Completed on X" for finished projects — field exists, needs filling |
| Project avatar / colour | Visual identity per project card |
| Sprint data from Jira Agile API | Auto-populate sprint dates instead of manual entry |

---

## 4. Layer 2 — Sprint Cards Grid

The main body of the Project Overview page. Displays all sprints as cards in a grid. Each card gives a full health snapshot without needing to click in.

### Layout

```
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│ Sprint 1  [Completed]           │  │ Sprint 2  [Completed]           │
│ Auth & Login Flow               │  │ Payment Integration             │
│ Jan 1 – Jan 14  (14 days)       │  │ Jan 15 – Jan 28  (14 days)      │
│ ────────────────────────────── │  │ ────────────────────────────── │
│ ████████████████░░  12/14  85% │  │ ████████████████████  10/10 100%│
│ Story pts: 34/40                │  │ Story pts: 28/28                │
│ Meetings: 4 · Commits: 23       │  │ Meetings: 3 · Commits: 31       │
│ Bugs: 2  ·  Carried: 0          │  │ Bugs: 1  ·  Carried: 0          │
│ [P] [S] [M] [N] +2              │  │ [P] [S] [M] [N] [A]             │
└─────────────────────────────────┘  └─────────────────────────────────┘

┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│ Sprint 3  [Completed]           │  │ ★ Sprint 4  [Active]            │
│ Refunds & Disputes              │  │ Reporting & Analytics           │
│ Jan 29 – Feb 11  (14 days)      │  │ Feb 12 – Feb 25  (14 days)      │
│ ────────────────────────────── │  │ ────────────────────────────── │
│ ██████████░░░░░░░  8/14   57%  │  │ ████████░░░░░░░░░░  6/12   50%  │
│ Story pts: 18/36  ⚠             │  │ Story pts: 16/32                │
│ Meetings: 5 · Commits: 18       │  │ 6 days left  ·  [⚠ At Risk]    │
│ Bugs: 3  ·  Carried: 2          │  │ Meetings: 2 · Commits: 14       │
│ [P] [S] [M] +3                  │  │ [P] [S] [M] [N] [A] [R]         │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

### Direct Fields Per Card

| Display | Table | Column | Notes |
|---|---|---|---|
| Sprint number | `sprints` | `sprint_number` | "Sprint 4" |
| Sprint name | `sprints` | `name` | Subtitle |
| Status badge | `sprints` | `status` | `planned` / `active` / `completed` |
| Start date | `sprints` | `start_date` | |
| End date | `sprints` | `end_date` | |
| Sprint goal | `sprints` | `goal` | 1-liner, truncated if long |

### Derived Stats Per Card

| Stat | How | Tables |
|---|---|---|
| Total tickets | `COUNT(*)` on `sprint_tickets` where `sprint_id = X` | `sprint_tickets` |
| Closed tickets | JOIN `jira_tickets`, filter `status = 'Done'` | `sprint_tickets` → `jira_tickets.status` |
| Completion % | `closed / total * 100` | Same |
| Progress bar | Visual fill of completion % | Same |
| Story points total | `SUM(story_points)` all sprint tickets | `sprint_tickets` → `jira_tickets.story_points` |
| Story points completed | `SUM(story_points)` where `status = 'Done'` | Same |
| Meeting count | `COUNT(*)` where `meeting_date BETWEEN start_date AND end_date` | `meetings.meeting_date` |
| Commit count | `entity_references` where `reference_id` IN sprint ticket keys, `source_type = 'commit'` | `entity_references` → `git_commits` |
| Bug count | COUNT where `issue_type = 'Bug'` | `jira_tickets.issue_type` |
| Carried over tickets | Tickets from this sprint also appearing in next sprint's `sprint_tickets` | `sprint_tickets` across consecutive sprints |
| Participant avatars | Deduplicated names from ticket assignees + meeting participants + commit authors | `jira_tickets.assignee`, `meetings.participants`, `git_commits.author_name` → `employees` |
| Duration in days | `end_date - start_date` | `sprints` |

### Active Sprint — Additional Fields

| Display | How | Tables |
|---|---|---|
| Days remaining | `end_date - today` | `sprints.end_date` |
| Time elapsed % | `(today - start_date) / (end_date - start_date) * 100` | `sprints` |
| At Risk flag | `time_elapsed% > completion% + 20` → show warning | Derived |

### Card Ordering & Behaviour

- **Active sprint** is always pinned first, with a star icon and highlighted border
- Remaining sprints ordered by `sprints.sprint_number` ascending
- `planned` sprints shown with greyed-out stats (no data yet)
- `completed` sprints shown in full — never hidden

### Velocity Trend Arrow (Per Card)

Compare completed story points of this sprint vs previous sprint:
- Higher → green up arrow with delta: `↑ +10 pts`
- Lower → red down arrow with delta: `↓ -6 pts`
- First sprint → no arrow

### Future Work

| Missing | Impact |
|---|---|
| Sprint data from Jira Agile API | Auto-populate `start_date`, `end_date`, `goal`, `status` |
| `sprint_tickets.added_date` population | Required for scope creep detection — field exists, needs filling during ingestion |
| Daily story point snapshots | Needed for proper burndown chart on card |

---

## 5. Layer 3 — Sprint Block Header

The top section of the sprint detail view. Appears after clicking a sprint card. Stays visible as the user switches between tabs. Acts as persistent context for all tabs below.

### Layout

```
◀ Payment Gateway                                        [Completed]

Sprint 4  ·  Reporting & Analytics
Feb 12, 2026  →  Feb 25, 2026   (14 days)

Goal: Build end-to-end reporting dashboard with export functionality

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│ 10/12     │  │ 28/32 pts │  │ 4 meetings│  │ 31 commits│  │ 3 decisions│
│ Tickets   │  │ Story Pts │  │           │  │           │  │            │
└───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Participants (7)
┌───────────────────────────────────────────────────────────────────┐
│  [P]  Preet       Backend Engineer    [Jira ✓] [Git ✓] [Mtg ✓]  │
│  [S]  Sarah       Product Manager     [Jira ✓] [Git  ] [Mtg ✓]  │
│  [M]  Marcus      Frontend Engineer   [Jira ✓] [Git ✓] [Mtg  ]  │
│  [N]  Nadia       QA Engineer         [Jira ✓] [Git  ] [Mtg ✓]  │
│  [A]  Alex        DevOps              [Jira  ] [Git ✓] [Mtg ✓]  │
│       + 2 more                                        [Show all] │
└───────────────────────────────────────────────────────────────────┘

[ Summary ]  [ Meetings ]  [ Tickets ]  [ Decisions & Velocity ]
```

### Active Sprint — Additional Bar

```
Feb 12 → Feb 25    6 days remaining
Time elapsed:   ████████████░░░░░░  71%
Work completed: ████████░░░░░░░░░░  50%   ⚠ At Risk
```

### Direct Fields

| Display | Table | Column | Notes |
|---|---|---|---|
| Sprint number | `sprints` | `sprint_number` | |
| Sprint name | `sprints` | `name` | |
| Status badge | `sprints` | `status` | |
| Start date | `sprints` | `start_date` | |
| End date | `sprints` | `end_date` | |
| Sprint goal | `sprints` | `goal` | Full text, prominent |
| Back link label | `sprints.project_id` → `projects` | `projects.name` | "◀ Payment Gateway" |

### Derived — Duration & Progress

| Display | How | Tables |
|---|---|---|
| Duration | `end_date - start_date` | `sprints` |
| Days remaining | `end_date - today` | `sprints.end_date` |
| Time elapsed % | `(today - start_date) / (end_date - start_date) * 100` | `sprints` |
| Work done % | Closed tickets / total tickets | `sprint_tickets` → `jira_tickets.status` |
| At Risk flag | `time_elapsed% > work_done% + 20` | Derived |

### Stats Bar — Derived

| Stat | How | Tables |
|---|---|---|
| Tickets closed / total | COUNT sprint_tickets, filter `status = 'Done'` | `sprint_tickets` → `jira_tickets.status` |
| Story points done / total | SUM `story_points` — all vs done | `sprint_tickets` → `jira_tickets.story_points` |
| Meeting count | COUNT where `meeting_date BETWEEN start_date AND end_date` | `meetings.meeting_date` |
| Commit count | `entity_references` where `reference_id` IN sprint ticket keys | `entity_references` → `git_commits` |
| Decision count | COUNT where `decision_date BETWEEN start_date AND end_date` | `decisions.decision_date` |

### Participants Block

Participants are derived from three sources and deduplicated:

| Source | Table | Column |
|---|---|---|
| Ticket assignees | `jira_tickets` | `assignee` |
| Ticket reporters | `jira_tickets` | `reporter` |
| Meeting attendees | `meetings` | `participants` — parsed, meetings filtered by sprint date range |
| Commit authors | `git_commits` | `author_name` — commits linked via `entity_references` to sprint tickets |
| Profile resolution | `employees` | `name`, `role`, `department` — matched by name string |

**Source icons per participant:**

| Icon | Condition |
|---|---|
| `Jira ✓` | Name found in `jira_tickets.assignee` or `.reporter` for this sprint |
| `Git ✓` | Name found in `git_commits.author_name` for commits linked to this sprint |
| `Mtg ✓` | Name found in `meetings.participants` for meetings in sprint date range |

**Display rules:**
- Default: show top 5 by ticket count, descending
- "Show all" expands to full list
- Unmatched names (not in `employees`) shown as raw string without role

### Additional Derived Features

- **Scope creep indicator** — `sprint_tickets.added_date > sprint.start_date`. Show "X tickets added after sprint started."
- **Most discussed ticket** — count ticket key occurrences across `meetings.raw_vtt_content` for sprint meetings. Surface top result as a callout.
- **Confluence activity** — COUNT `confluence_pages` where `page_updated_date BETWEEN start_date AND end_date`. Show as "X docs updated."

### Future Work

| Missing | Impact |
|---|---|
| `meeting_type` field on `meetings` | Stats bar could show "4 meetings (2 standups, 1 planning, 1 review)" |
| Explicit `sprint_id` FK on `meetings` | More reliable than inferring by date range |

---

## 6. Layer 4 — Tab 1: AI Sprint Summary

The first and anchor tab. A person should be able to read this tab alone and understand the entire sprint. All content is AI-generated from the four data sources.

### Layout

```
[ Summary ✦ ]  [ Meetings ]  [ Tickets ]  [ Decisions & Velocity ]

┌──────────────────────────────────────────────────────────────────────┐
│ ✦ AI Generated Summary                                              │
│ Confidence: 84% ████████░░                                          │
│ Generated Mar 1, 2026 at 10:42 AM                                   │
│ Sources: 12 tickets · 4 meetings · 31 commits · 2 docs              │
│                                               [Regenerate ↺]        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ What we accomplished                                                 │
│ ─────────────────────                                                │
│ The team delivered the core reporting dashboard, completing 10 of    │
│ 12 planned tickets (87.5% story points)...                          │
│                                                                      │
│ Key decisions made                                                   │
│ ──────────────────                                                   │
│ • Chose Recharts over D3 for dashboard rendering  [Architecture]    │
│ • PDF export deferred to Sprint 5  [Process]                        │
│                                                                      │
│ What was discussed in meetings                                       │
│ ────────────────────────────────                                     │
│ Sprint planning aligned the team on scope. Mid-sprint standup        │
│ flagged the PDF export risk early...                                │
│                                                                      │
│ Code changes                                                         │
│ ────────────                                                         │
│ 31 commits across 18 files. Heavy activity in /src/reports...       │
│                                                                      │
│ Open items carried forward                                           │
│ ───────────────────────────                                          │
│ 2 tickets remain open: PAY-211 (PDF Export), PAY-215 (CSV bulk)     │
│                                                                      │
│ Team contribution                                                    │
│ ─────────────────                                                    │
│  Preet    6 tickets · 18 pts · 14 commits                           │
│  Marcus   3 tickets · 8 pts  · 12 commits                           │
│  Nadia    4 tickets · 12 pts · 0 commits  (QA)                      │
│  Sarah    — tickets · — pts  · 0 commits  (PM, 4 meetings)          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Metadata Bar

| Element | Table | Column | Notes |
|---|---|---|---|
| Confidence score | `sprints` | `summary_confidence` | Future field |
| Generated timestamp | `sprints` | `summary_generated_at` | Future field |
| Ticket count | `sprint_tickets` | COUNT | |
| Meeting count | `meetings` | COUNT where date in range | |
| Commit count | `entity_references` → `git_commits` | COUNT | |
| Doc count | `confluence_pages` | COUNT where `page_updated_date` in range | |

### Confidence Calculation

Weighted score based on data quality:

| Signal | Weight | How |
|---|---|---|
| Tickets with descriptions filled | 30% | `jira_tickets.description` not null / total sprint tickets |
| Meetings with summaries filled | 30% | `meetings.summary` not null / total sprint meetings |
| Commit messages are descriptive | 20% | avg character length of `git_commits.message` |
| Decision rationale filled | 20% | `decisions.rationale` not null / total sprint decisions |

### Section 1: What We Accomplished

| Data | Table | Column |
|---|---|---|
| Closed ticket titles | `jira_tickets` | `summary` where `status = 'Done'` |
| Ticket descriptions | `jira_tickets` | `description` |
| Story points weight | `jira_tickets` | `story_points` |
| Issue type context | `jira_tickets` | `issue_type` |
| Epic grouping | `jira_tickets` | `epic_link` |

All filtered through `sprint_tickets` for current sprint. AI groups by epic or type to avoid a flat list.

### Section 2: Key Decisions Made

| Data | Table | Column |
|---|---|---|
| Decision titles | `decisions` | `title` |
| Decision context | `decisions` | `description`, `rationale` |
| Category label | `decisions` | `category` |
| Source attribution | `decisions` | `source_type`, `source_title` |

Filtered by `decisions.decision_date BETWEEN sprint.start_date AND sprint.end_date`.

### Section 3: What Was Discussed in Meetings

| Data | Table | Column |
|---|---|---|
| Meeting summaries | `meetings` | `summary` |
| Key decisions per meeting | `meetings` | `key_decisions` |
| Action items | `meetings` | `action_items` |
| Meeting titles and dates | `meetings` | `title`, `meeting_date` |

Filtered by `meetings.meeting_date BETWEEN sprint.start_date AND sprint.end_date`.

### Section 4: Code Changes

| Data | Table | Column |
|---|---|---|
| Commit messages | `git_commits` | `message` |
| Files changed | `git_commit_files` | `filename`, `additions`, `deletions` |
| Commit authors | `git_commits` | `author_name` |
| Commit dates | `git_commits` | `commit_date` |

Commits fetched via `entity_references` where `reference_id` IN sprint ticket keys. Only commits linked to sprint work are included.

### Section 5: Open Items Carried Forward

| Data | Table | Column |
|---|---|---|
| Unresolved tickets | `jira_tickets` | `status` ≠ `'Done'` via `sprint_tickets` |
| Ticket summaries | `jira_tickets` | `summary`, `issue_key` |
| Unresolved action items | `meetings` | `action_items` |
| Story points at risk | `jira_tickets` | `story_points` where not done |

### Section 6: Team Contribution

| Data | Table | Column |
|---|---|---|
| Tickets per person | `jira_tickets` | `assignee` — COUNT per name |
| Story points per person | `jira_tickets` | `story_points` — SUM per assignee |
| Commits per person | `git_commits` | `author_name` — COUNT |
| Meeting attendance | `meetings` | `participants` — presence check per sprint meeting |
| Role context | `employees` | `name`, `role` |

### Additional Features Using Existing Data

- **Busiest day callout** — group `git_commits.commit_date` by day, find MAX count. "Most active day: Feb 19 with 9 commits."
- **Most discussed ticket** — count ticket key occurrences across all `meetings.raw_vtt_content` in sprint. Surface top 3.
- **Commit message themes** — word frequency on `git_commits.message` ("fix", "add", "refactor") shows what type of work dominated.
- **Files most touched** — `git_commit_files.filename` aggregated by COUNT. "18 changes in /src/reports, 9 in /api/exports."

### Future Work

| Missing | What to add |
|---|---|
| `sprints.summary_text` | Cache generated summary — avoids regenerating on every load |
| `sprints.summary_generated_at` | Timestamp for display and staleness detection |
| `sprints.summary_confidence` | Stored confidence score |
| Stale detection | Hash of source data — show "Data updated since last generation" if changed |
| Confluence → sprint linking | Currently inferred by date range — not guaranteed to be sprint-related |

---

## 7. Layer 5 — Tab 2: Meetings

All meetings that occurred during the sprint date range. Default view shows all meetings as collapsible cards, most recent first. Each card has two levels of depth — inline summary and full transcript.

### Layout

```
[ Summary ]  [ Meetings 4 ]  [ Tickets ]  [ Decisions & Velocity ]

┌──────────────────────────────────────────────────────────────────────┐
│  Filter: [All types ▾]  [All participants ▾]          4 meetings    │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ [Planning]  Sprint 4 Planning                                        │
│ Feb 12, 2026  ·  1h 23m  ·  6 participants                          │
│ Preet  Sarah  Marcus  Nadia  Alex  +1                               │
│ 3 decisions · 5 action items · PAY-201  PAY-202  PAY-203            │
│                                                                      │
│ Summary ▾                                                            │
│  AI Generated  ·  Confidence: 88% █████████░  ·  [Regenerate]      │
│  The team aligned on the reporting dashboard scope...               │
│                                                                      │
│ Key decisions ▾                                                      │
│  • Chose Recharts for dashboard (Technology)                        │
│  • PDF export is a stretch goal (Process)                           │
│                                                                      │
│ Action items ▾                                                       │
│  • Preet: Set up Recharts boilerplate by Feb 14                     │
│  • Sarah: Confirm export requirements with stakeholder              │
│                                                                      │
│                              [View Full Transcript →]               │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ [Standup]  Mid-Sprint Check-in                     [collapsed ▸]    │
│ Feb 18, 2026  ·  32m  ·  5 participants                             │
└──────────────────────────────────────────────────────────────────────┘
```

### Meeting Card — Direct Fields

| Display | Table | Column | Notes |
|---|---|---|---|
| Meeting title | `meetings` | `title` | |
| Meeting date | `meetings` | `meeting_date` | Formatted "Feb 12, 2026" |
| Duration | `meetings` | `duration_seconds` | Formatted to "1h 23m" |
| Meeting type badge | `meetings` | `meeting_type` | **Future field** — Planning / Standup / Review / Retro / Ad-hoc |
| Summary text | `meetings` | `summary` | AI generated, shown expanded |
| Summary confidence | `meetings` | `summary_confidence` | **Future field** |
| Key decisions | `meetings` | `key_decisions` | AI extracted, shown expanded |
| Decisions confidence | `meetings` | `decisions_confidence` | **Future field** |
| Action items | `meetings` | `action_items` | AI extracted, shown expanded |
| Action items confidence | `meetings` | `action_items_confidence` | **Future field** |

### Meeting Card — Derived Fields

| Display | How | Tables |
|---|---|---|
| Participant names and count | Parse `meetings.participants`, match to `employees.name` | `meetings.participants` → `employees` |
| Ticket reference chips | `entity_references` where `source_type = 'meeting'` and `source_id = meeting.id` | `entity_references.reference_id` |
| Decision count | COUNT `decisions` where `source_type = 'meeting'` and `source_id = meeting.id` | `decisions` |
| Action item count | Count line items in `meetings.action_items` text | `meetings.action_items` |

### Full Transcript View

Opened via "View Full Transcript →" button. Renders `meetings.raw_vtt_content` in readable format.

```
┌──────────────────────────────────────────────────────┐
│ Sprint 4 Planning  ·  Feb 12  ·  1h 23m             │
│ ─────────────────────────────────────────────────── │
│ [00:00:12]  Preet:   Okay let's get started...      │
│ [00:00:45]  Sarah:   The goal this sprint is...     │
│ [00:02:13]  Marcus:  I have a question about...     │
│ [00:04:50]  Preet:   PAY-201 is the main...    ───→ ticket chip │
│                                                     │
│  🔍 Search transcript...                            │
│  Filter by speaker: [All ▾]                         │
└──────────────────────────────────────────────────────┘
```

| Element | Table | Column |
|---|---|---|
| Speaker, timestamp, text | `meetings` | `raw_vtt_content` — parsed from VTT |
| Inline ticket highlights | `entity_references` | `reference_id` — matched to text |

### Tab-Level Filters

| Filter | How | Column |
|---|---|---|
| Meeting type | Filter by `meeting_type` badge | `meetings.meeting_type` — future field |
| Participant | Show only meetings where name appears in `participants` | `meetings.participants` |

### Additional Features Using Existing Data

- **Most talkative meeting** — sort by `duration_seconds`. Flag the longest meeting.
- **Ticket discussion frequency** — count ticket key mentions across all `raw_vtt_content` for sprint meetings. "PAY-201 was mentioned in 3 of 4 meetings."
- **Meeting attendance rate** — participant count per meeting vs total sprint participants. "6/8 sprint members attended."
- **Decisions per meeting rank** — `decisions.source_id` count per meeting. Shows which meetings were most impactful.

### Future Work

| Missing | Impact |
|---|---|
| `meetings.meeting_type` | Cannot distinguish planning vs standup vs retro without this |
| Structured `action_items` JSON | Currently free text — owners cannot be linked to employees |
| Action item status tracking | No way to know if an action item was resolved — needs `action_items` table |
| Explicit `sprint_id` on meetings | Currently meetings are linked to sprints by date range — explicit FK is more reliable |

---

## 8. Layer 6 — Tab 3: Tickets

All tickets in the sprint. Default shows closed tickets first. Toggle to see all. Grouped by status. Expandable rows show deep linked context.

### Layout

```
[ Summary ]  [ Meetings ]  [ Tickets 12 ]  [ Decisions & Velocity ]

┌──────────────────────────────────────────────────────────────────────┐
│  Done: 10  In Progress: 1  Open: 1  Blocked: 0                     │
│  Story pts: 28/32  ·  Bugs: 2  ·  Avg cycle time: 4.2 days         │
│  ████████████████████████░░░░  87.5%                                 │
└──────────────────────────────────────────────────────────────────────┘

Group by: [Status ▾]   [All types ▾]  [All assignees ▾]  [Priority ▾]
                                       [● Closed first]  [○ All tickets]

━━  Done (10)  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────────────┐
│ ✅ PAY-201  [Story] [High]   Reporting dashboard core layout   [P]  │
│ 5 pts  ·  Closed in 6 days  ·  Feb 12 → Feb 18  ·  3 commits   ▾  │
├──────────────────────────────────────────────────────────────────────┤
│  Description: Integrate Recharts, build reusable chart wrapper...   │
│                                                                      │
│  Linked commits (3)                                                  │
│  a3f92c1  Marcus  "feat: add chart wrapper"  Feb 15                 │
│                                                                      │
│  Discussed in meetings (2)                                           │
│  Sprint Planning · Feb 12  ·  Sprint Review · Feb 24               │
│                                                                      │
│  Related decisions (1)                                               │
│  → Chose Recharts over D3 for dashboard rendering  [Architecture]  │
└──────────────────────────────────────────────────────────────────────┘
```

### Stats Bar — Derived

| Display | How | Table | Column |
|---|---|---|---|
| Done count | COUNT where `status = 'Done'` | `sprint_tickets` → `jira_tickets` | `status` |
| In Progress count | COUNT where `status = 'In Progress'` | same | `status` |
| Open count | COUNT where `status = 'To Do'` | same | `status` |
| Blocked count | COUNT where `status = 'Blocked'` | same | `status` |
| Story points completed / total | SUM with and without status filter | `jira_tickets` | `story_points` |
| Bug count | COUNT where `issue_type = 'Bug'` | `jira_tickets` | `issue_type` |
| Avg cycle time | AVG of `resolved_date - created_date` where done | `jira_tickets` | `resolved_date`, `created_date` |

### Ticket Row — Direct Fields

| Display | Table | Column | Notes |
|---|---|---|---|
| Issue key | `jira_tickets` | `issue_key` | Clickable — links to Jira |
| Issue type badge | `jira_tickets` | `issue_type` | Story / Bug / Task / Epic |
| Priority badge | `jira_tickets` | `priority` | Critical / High / Medium / Low |
| Ticket summary | `jira_tickets` | `summary` | Main title |
| Assignee | `jira_tickets` | `assignee` | Initial avatar, hover for full name |
| Story points | `jira_tickets` | `story_points` | |
| Status icon | `jira_tickets` | `status` | ✅ Done / 🔄 In Progress / ○ Open / 🚫 Blocked |
| Created date | `jira_tickets` | `created_date` | |
| Resolved date | `jira_tickets` | `resolved_date` | Null if not done |
| Labels | `jira_tickets` | `labels` | Chips |
| Epic | `jira_tickets` | `epic_link` | Small chip |

### Ticket Row — Derived Fields

| Display | How | Tables |
|---|---|---|
| Cycle time | `resolved_date - created_date` in days | `jira_tickets` |
| Ongoing days | `today - created_date` for in-progress tickets | `jira_tickets.created_date` |
| Commit count | COUNT `entity_references` where `reference_id = issue_key` and `source_type = 'commit'` | `entity_references` |
| Scope creep flag | `sprint_tickets.added_date > sprint.start_date` | `sprint_tickets.added_date`, `sprints.start_date` |

### Ticket Expanded View

| Display | How | Tables |
|---|---|---|
| Full description | Direct | `jira_tickets.description` |
| Comments | Direct, parsed | `jira_tickets.comments` |
| Linked commits | `entity_references` where `source_type = 'commit'`, `reference_id = issue_key` | `entity_references` → `git_commits.sha`, `git_commits.message`, `git_commits.author_name`, `git_commits.commit_date` |
| Discussed in meetings | `entity_references` where `source_type = 'meeting'`, `reference_id = issue_key` | `entity_references` → `meetings.title`, `meetings.meeting_date` |
| Related decisions | `decisions.related_tickets` array contains `issue_key` | `decisions.title`, `decisions.category` |
| Reporter | Direct | `jira_tickets.reporter` |

### Grouping Options

| Group by | How |
|---|---|
| Status (default) | Group by `jira_tickets.status` — Done section shown first |
| Assignee | Group by `jira_tickets.assignee` — shows per-person workload |
| Issue type | Group by `jira_tickets.issue_type` |
| Epic | Group by `jira_tickets.epic_link` |

### Filters

| Filter | Column |
|---|---|
| Issue type | `jira_tickets.issue_type` |
| Assignee | `jira_tickets.assignee` |
| Priority | `jira_tickets.priority` |
| Label | `jira_tickets.labels` |

### Additional Features Using Existing Data

- **Commit-less tickets** — tickets with zero linked commits in `entity_references`. Flag with "no commits" chip. Useful for spotting undocumented work.
- **Most commented ticket** — count line items in `jira_tickets.comments` per ticket. Surface most discussed.
- **Bug vs feature donut** — `jira_tickets.issue_type` breakdown as small chart in stats bar.
- **Cycle time comparison** — this sprint avg vs previous sprint avg. Both derivable from `resolved_date - created_date`.
- **Unassigned tickets** — `jira_tickets.assignee` is null. Flag in open/in-progress section.

### Future Work

| Missing | Impact |
|---|---|
| `sprint_tickets.added_date` population | Scope creep detection — field exists, needs filling during ingestion |
| Structured `comments` field | `jira_tickets.comments` is raw text — needs standardisation for clean display |
| Ticket status history table | Cannot show when a ticket moved between states |
| Blocked reason field | Blocked status captured but reason is not stored |

---

## 9. Layer 7 — Tab 4: Decisions & Velocity

Two sections. Decisions first — the "why" record of the sprint. Velocity second — the "how much" and "who" breakdown.

### Layout

```
[ Summary ]  [ Meetings ]  [ Tickets ]  [ Decisions & Velocity ]

━━  Decisions (5)  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Group by: [Category ▾]   [All sources ▾]  [All statuses ▾]

── Architecture (1) ─────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────┐
│ [Architecture]  [Active]                                         │
│ Recharts chosen over D3 for dashboard rendering                  │
│ Decided by: Preet, Marcus  ·  Feb 12  ·  Source: Sprint Planning │
│ Confidence: 91% ████████████░                                    │
│                                                                  │
│ Rationale ▾                                                      │
│  D3 offers more flexibility but requires significantly more      │
│  implementation time...                                          │
│                                                                  │
│ Alternatives considered ▾                                        │
│  D3.js — too much custom implementation overhead                 │
│  Victory — limited TypeScript support                            │
│                                                                  │
│ Impact ▾                                                         │
│  Reduces frontend build time by ~3 days. May limit advanced      │
│  chart customisation in future sprints...                        │
│                                                                  │
│ Related tickets: [PAY-202]  [PAY-205]                           │
└──────────────────────────────────────────────────────────────────┘

── Process (2) ──────────────────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────┐
│ [Process]  [Superseded]                                          │
│ ~~QA will manually review all chart components before merge~~   │
│ Superseded by → QA review moved to automated testing pipeline   │
│ Feb 13  ·  Source: Sprint Planning                               │
└──────────────────────────────────────────────────────────────────┘

━━  Velocity & Metrics  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────────┐
│ Story Points                                                     │
│  Planned       32 pts  ████████████████████████████████         │
│  Completed     28 pts  ████████████████████████████░░░░  87.5%  │
│  Carried over   4 pts  ████░  (PAY-211, PAY-215)               │
│  vs Sprint 3:  18 pts completed  ↑ +10 pts                      │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ Team Contribution                                                │
│  Name     Tickets  Story Pts  Commits  Meetings  Cycle time     │
│  ──────────────────────────────────────────────────────────     │
│  Preet       6       18 pts     14        3        3.8 days     │
│  Marcus      3        8 pts     12        2        4.5 days     │
│  Nadia       4       12 pts      0        4        4.0 days     │
│  Sarah       0        —          0        4          —          │
│  Alex        0        —          5        2          —          │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ Sprint Metrics                                                   │
│  Bug rate           2 / 12 tickets   16.6%                       │
│  Scope creep        2 tickets added after sprint start           │
│  Commit peak        Feb 19 — 9 commits                          │
│  Files most changed /src/reports (18)  /api/exports (9)         │
└──────────────────────────────────────────────────────────────────┘
```

### Section 1: Decisions — Direct Fields

Filtered by `decisions.decision_date BETWEEN sprint.start_date AND sprint.end_date`.

| Display | Table | Column |
|---|---|---|
| Decision title | `decisions` | `title` |
| Category badge | `decisions` | `category` |
| Status badge | `decisions` | `status` |
| Decision date | `decisions` | `decision_date` |
| Decided by | `decisions` | `decided_by` — array, rendered as names |
| Source label | `decisions` | `source_title` |
| Source type icon | `decisions` | `source_type` |
| Rationale | `decisions` | `rationale` — expandable |
| Alternatives considered | `decisions` | `alternatives_considered` — expandable |
| Impact | `decisions` | `impact` — expandable |
| Related tickets | `decisions` | `related_tickets` — array, rendered as chips |
| Confidence score | `decisions` | `confidence_score` |
| Superseded by link | `decisions` | `superseded_by` — FK to another decision |
| Supersedes link | `decisions` | `supersedes` — FK to another decision |

### Decision Source Deep Links

| `source_type` | Links to |
|---|---|
| `meeting` | `decisions.source_id` → `meetings.id` — opens meeting in Tab 2 |
| `confluence` | `decisions.source_id` → `confluence_pages.id` |
| `jira` | `decisions.source_id` → `jira_tickets.id` — opens ticket in Tab 3 |
| `git_commit` | `decisions.source_id` → `git_commits.id` |

### Decisions — Grouping & Filters

**Group by:**

| Option | How |
|---|---|
| Category (default) | `decisions.category` |
| Source | `decisions.source_type` |
| Status | Active first, then Proposed, then Superseded / Reversed |
| Date | Chronological order |

**Filters:**

| Filter | Column |
|---|---|
| Source type | `decisions.source_type` |
| Status | `decisions.status` |
| Category | `decisions.category` |
| Decided by | `decisions.decided_by` array contains name |

### Superseded Decisions — Visual Treatment

Superseded decisions are shown with:
- Strikethrough on title
- Grey / muted card style
- "Superseded by →" link to the replacing decision
- Both directions navigable via `decisions.superseded_by` and `decisions.supersedes`

### Section 2: Velocity — Story Points

| Display | How | Table | Column |
|---|---|---|---|
| Planned story points | SUM all sprint tickets | `sprint_tickets` → `jira_tickets` | `story_points` |
| Completed story points | SUM where `status = 'Done'` | `jira_tickets` | `story_points`, `status` |
| Carried over points | SUM where `status != 'Done'` | `jira_tickets` | `story_points`, `status` |
| Carried over ticket keys | `issue_key` where `status != 'Done'` | `jira_tickets` | `issue_key` |
| Previous sprint completed | SUM for sprint N-1 | `sprints` + `sprint_tickets` → `jira_tickets` | `sprint_number` |
| Velocity delta | current - previous | Derived | |

### Section 2: Velocity — Team Contribution Table

| Column | How | Table | Column |
|---|---|---|---|
| Name | Resolve from employee profile | `employees` | `name` |
| Tickets closed | COUNT where `assignee = name` and `status = 'Done'` | `jira_tickets` | `assignee`, `status` |
| Story points | SUM where `assignee = name` and `status = 'Done'` | `jira_tickets` | `story_points` |
| Commits | COUNT where `author_name` matches employee | `git_commits` | `author_name` |
| Meetings attended | COUNT meetings in sprint range where name in participants | `meetings` | `participants`, `meeting_date` |
| Avg cycle time | AVG(`resolved_date - created_date`) for their closed tickets | `jira_tickets` | `resolved_date`, `created_date` |

### Section 2: Velocity — Sprint Metrics

| Display | How | Table | Column |
|---|---|---|---|
| Bug rate | COUNT `issue_type = 'Bug'` / total | `jira_tickets` | `issue_type` |
| Scope creep | COUNT where `added_date > sprint.start_date` | `sprint_tickets` | `added_date` |
| Peak commit day | GROUP BY `DATE(commit_date)`, MAX COUNT | `git_commits` | `commit_date` |
| Files most changed | GROUP BY `filename`, COUNT, top 3 | `git_commit_files` | `filename` |

### Additional Features Using Existing Data

- **Decision source breakdown** — COUNT by `source_type`. "3 from meetings, 1 from Confluence, 1 from commit." Shows where decisions are being made.
- **Superseded decision chain** — if a decision was both created and superseded in this sprint, render as a connected pair with an arrow.
- **Contributor balance** — if one person has >50% of closed tickets, surface as a subtle callout. Derivable from `jira_tickets.assignee` counts.
- **Zero-commit contributors** — people with tickets but no commits visible in table. Context provided by `employees.role`.

### Future Work

| Missing | Impact |
|---|---|
| Velocity trend chart (3+ sprints) | Only meaningful once multiple completed sprints are populated |
| Daily burndown snapshots | Requires `sprint_burndown_snapshots` table with daily story point records |
| `sprint_tickets.added_date` population | Scope creep metric — field exists, needs filling |
| `decided_by` → Employee FK | Currently array of name strings — name matching needed |

---

## 10. Future Work Summary

All items flagged across layers, consolidated:

### Database Changes Required

| Change | Layer | Priority |
|---|---|---|
| `meetings.meeting_type` enum field | Layers 3, 5 | High — needed to distinguish meeting types |
| `meetings.summary_confidence` FloatField | Layers 4, 5 | High — AI confidence standard |
| `meetings.decisions_confidence` FloatField | Layer 5 | High — AI confidence standard |
| `meetings.action_items_confidence` FloatField | Layer 5 | High — AI confidence standard |
| `sprints.summary_text` TextField | Layer 4 | High — cache AI summary |
| `sprints.summary_generated_at` DateTimeField | Layer 4 | High — display and staleness detection |
| `sprints.summary_confidence` FloatField | Layer 4 | High — AI confidence standard |
| `sprint_tickets.added_date` population | Layers 2, 6, 7 | Medium — scope creep detection |
| `meetings.sprint_id` FK | Layers 3, 5 | Medium — more reliable than date range matching |
| `sprint_burndown_snapshots` table | Layer 7 | Low — burndown chart |
| Ticket status history table | Layer 6 | Low — state change tracking |

### External Integration Required

| Integration | Layer | Priority |
|---|---|---|
| Jira Agile API for sprint data | Layers 2, 3 | High — eliminates manual sprint entry |
| Jira sprint auto-sync | Layers 2, 3 | High — `start_date`, `end_date`, `goal`, `status` from Jira |

### Logic / Matching Improvements

| Improvement | Layer | Priority |
|---|---|---|
| `decided_by` names → Employee FK resolution | Layer 7 | Medium |
| Meeting participant name matching improvements | Layers 3, 5 | Medium |
| Structured action items JSON format | Layer 5 | Medium |
| Structured comments parsing | Layer 6 | Low |

---

## 11. Data Model Quick Reference

Summary of all tables used on this page and the columns accessed:

### `projects`
`id`, `name`, `description`, `status`, `owner`, `github_repo`, `jira_project_key`, `confluence_space_key`, `start_date`, `target_end_date`, `actual_end_date`, `tags`

### `sprints`
`id`, `sprint_number`, `name`, `start_date`, `end_date`, `goal`, `status`, `project_id`
*(Future: `summary_text`, `summary_generated_at`, `summary_confidence`)*

### `sprint_tickets`
`id`, `sprint_id`, `ticket_id`, `added_date`

### `jira_tickets`
`id`, `issue_key`, `issue_type`, `summary`, `description`, `status`, `priority`, `assignee`, `reporter`, `created_date`, `updated_date`, `resolved_date`, `labels`, `epic_link`, `sprint`, `story_points`, `comments`

### `meetings`
`id`, `title`, `meeting_date`, `raw_vtt_content`, `summary`, `key_decisions`, `action_items`, `participants`, `duration_seconds`, `source_filename`
*(Future: `meeting_type`, `sprint_id`, `summary_confidence`, `decisions_confidence`, `action_items_confidence`)*

### `git_commits`
`id`, `sha`, `author_name`, `author_email`, `commit_date`, `message`

### `git_commit_files`
`id`, `commit_id`, `filename`, `additions`, `deletions`, `status`

### `entity_references`
`id`, `source_type`, `source_id`, `reference_type`, `reference_id`

### `decisions`
`id`, `title`, `description`, `decision_date`, `rationale`, `alternatives_considered`, `impact`, `decided_by`, `source_type`, `source_id`, `source_title`, `related_tickets`, `related_decisions`, `category`, `status`, `superseded_by`, `supersedes`, `confidence_score`, `tags`

### `employees`
`id`, `name`, `email`, `role`, `department`, `jira_account_id`, `github_username`, `is_active`

### `confluence_pages`
`id`, `title`, `space`, `author`, `content`, `labels`, `page_created_date`, `page_updated_date`
