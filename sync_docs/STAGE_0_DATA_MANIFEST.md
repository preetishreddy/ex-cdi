# Project Osmosis — Stage 0: Synthetic Data Manifest

## Timeline
**One week: Monday January 13 – Friday January 17, 2025**
Alex Kim (new hire) joins **Monday January 20** — not present in any data.

## Cast (6 people in the data)
| Person | Role | Primary Domain |
|--------|------|---------------|
| Sarah Chen | Staff Architect | Architecture decisions, infra ownership |
| Dave Rossi | Senior Backend Dev | legacy_billing sole owner, going on leave Jan 27 |
| Priya Sharma | Senior Frontend Dev | Merchant dashboard redesign |
| Marcus Thompson | Platform / DevOps Engineer | CI/CD, rate limiting, infrastructure |
| Lisa Park | Mid-level Backend Dev | Ramping on billing, cross-cutting |
| James O'Brien | Engineering Manager | Resourcing, process, risk awareness |

## Storylines
| Story | Sources Involved | Drift/Gap? |
|-------|-----------------|------------|
| A: Jenkins → GitHub Actions | Confluence ✗, Jira ✓, Meetings ✓, Git ✓ | **DRIFT**: Wiki says Jenkins, meeting says GH Actions |
| B: Stripe Retry Meltdown | Confluence ✗, Jira ✓, Meetings ✓, Git ✓ | Wiki doesn't cover retry details |
| C: Merchant Dashboard Redesign | Confluence ✗, Jira ✓, Meetings ✓, Git ✓ | **DRIFT**: Design doc says REST, meeting says WebSocket |
| D: Rate Limiting Debate | Confluence ✗, Jira ✓, Meetings ✓, Git ✓ | **GAP**: No Confluence page for rate limiting |
| E: Latency Incident | Confluence partial, Jira ✓, Meetings ✓, Git ✓ | **GAP**: No monitoring/alerting runbook |
| F: Dave's Knowledge Risk | Confluence partial, Jira ✓, Meetings ✓, Git ✓ | Dave is sole owner, leaving soon |

## Generated Files

### Confluence (6 `.md` files)
| File | Last Updated | Key Detail |
|------|-------------|------------|
| `deployment-guide.md` | 2024-11-15 | **OUTDATED** — says Jenkins |
| `billing-system-overview.md` | 2024-08-05 | High-level, no retry logic details |
| `merchant-dashboard-design.md` | 2024-12-18 | **OUTDATED** — says REST polling |
| `api-gateway-runbook.md` | 2025-01-06 | Reasonably current |
| `onboarding-checklist.md` | 2024-09-20 | Generic, no billing-specific guide |
| `team-working-agreements.md` | 2024-11-01 | Process docs, meeting cadence |

### Jira (26 tickets in `.csv`)
- PAY-201 to PAY-228 (no PAY-209, PAY-214)
- Assignee spread: Dave (7), Marcus (6), Priya (6), Lisa (5), Sarah (1), James (1)
- Statuses: Done (9), In Progress (7), To Do (10)

### Meetings (5 `.vtt` files)
| File | Day | Key Decisions |
|------|-----|--------------|
| `2025-01-13_architecture-review.vtt` | Mon | Jenkins deprecated, rate limiting debate starts |
| `2025-01-14_standup.vtt` | Tue | Dave explains retry fix, Lisa ramping on webhooks |
| `2025-01-15_incident-debrief.vtt` | Wed | Deep dive on retry failure, monitoring gaps surface |
| `2025-01-16_architecture-review.vtt` | Thu | Token bucket decided, WebSocket switch, latency fix |
| `2025-01-17_standup.vtt` | Fri | Dave announces leave, new hire mentioned |

### Git (20 commits in `commits.json` + 13 code/config files)
**Commits by author:** Dave (7), Priya (4), Marcus (5), Lisa (2), Sarah (1)

**Code files:**
- `billing/retry_handler.py` — Dave's exponential backoff implementation
- `billing/stripe_webhook.py` — Webhook handler with DLQ + clock skew fix
- `billing/models.py` — SQLAlchemy models
- `billing/utils/resilience.py` — Shared retry/circuit breaker utility
- `billing/webhook_dlq.py` — Lisa's dead letter queue
- `billing/migrations/003_add_payment_index.sql` — Lisa's latency fix
- `.github/workflows/deploy-production.yml` — Marcus's GH Actions workflow
- `Jenkinsfile` — Deprecated, still in repo
- `platform_infra/rate_limiter.py` — Marcus's token bucket implementation
- `platform_infra/docs/adr/007-token-bucket-rate-limiting.md` — Sarah's ADR
- `merchant_dashboard/src/components/TransactionList.tsx` — Priya's component
- `merchant_dashboard/src/hooks/useTransactionSocket.ts` — Priya's WebSocket hook

## Cross-Reference Verification
| Event | Confluence | Jira | Meeting | Git |
|-------|-----------|------|---------|-----|
| Jenkins → GH Actions | `deployment-guide.md` says Jenkins | PAY-201,202,203,218 | Mon + Fri meetings | `deploy-production.yml`, deprecated `Jenkinsfile` |
| Retry meltdown | `billing-overview.md` doesn't cover it | PAY-204,205,219 | Tue standup, Wed debrief | `retry_handler.py`, `resilience.py` |
| Dashboard REST→WebSocket | `dashboard-design.md` says REST | PAY-210,211,212,225 | Thu review: Priya switches | `TransactionList.tsx`, `useTransactionSocket.ts` |
| Token bucket decision | **NO PAGE** | PAY-215,216,217,228 | Mon debate + Thu decision | `rate_limiter.py`, ADR-007 |
| Latency incident | Runbook mentions billing latency generally | PAY-207,208 | Thu review: Lisa presents fix | `003_add_payment_index.sql` |
| Webhook DLQ | **NOT MENTIONED** | PAY-206,222 | Wed debrief: events silently dropped | `webhook_dlq.py`, `stripe_webhook.py` |
| Dave key person risk | Ownership listed in docs | 7 tickets assigned to Dave | Wed + Fri: "only person", leave announced | 7/20 commits by Dave |
