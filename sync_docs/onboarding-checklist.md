---
title: "New Engineer Onboarding Checklist"
space: "Payments Platform"
author: "James O'Brien"
created: "2025-02-01"
last_updated: "2025-09-20"
labels: ["onboarding", "new-hire", "setup"]
version: 4
---

# New Engineer Onboarding Checklist

## Week 1: Environment & Access Setup

### Day 1
- [ ] Receive laptop and complete IT security training
- [ ] Set up GitHub account and request access to `meridiantech/payments-platform` repository
- [ ] Set up Jira account and join the "Payments Platform" project board
- [ ] Set up Confluence account and bookmark the Payments Platform space
- [ ] Join Slack channels: #payments-platform, #payments-alerts, #engineering-general
- [ ] Schedule 1:1 with your Engineering Manager (James O'Brien)

### Day 2–3
- [ ] Clone the payments-platform repository and follow the README setup instructions
- [ ] Run the local development environment using Docker Compose
- [ ] Complete the AWS onboarding request form for staging environment access
- [ ] Read the [Production Deployment Guide](./deployment-guide.md)
- [ ] Read the [API Gateway Runbook](./api-gateway-runbook.md)

### Day 4–5
- [ ] Shadow a senior engineer during a deployment (coordinate with Marcus Thompson)
- [ ] Pick up your first starter ticket from the Jira backlog (labeled `good-first-issue`)
- [ ] Submit your first PR and go through the code review process
- [ ] Attend your first team standup

## Week 2: System Deep Dive

- [ ] Read the [Legacy Billing System Overview](./billing-system-overview.md)
- [ ] Read the [Merchant Dashboard Design Document](./merchant-dashboard-design.md)
- [ ] Schedule a system walkthrough with the relevant service owner
- [ ] Complete your first code review for another team member

## Key Contacts

| Topic | Contact |
|-------|---------|
| General onboarding questions | James O'Brien |
| Repository and CI/CD setup | Marcus Thompson |
| Billing system walkthrough | Dave Rossi |
| Frontend / Dashboard questions | Priya Sharma |
| Architecture questions | Sarah Chen |

## Notes

- If any step is blocked, post in #payments-platform immediately
- Your onboarding buddy will be assigned on your first day
- Aim to have your local environment fully functional by end of Day 3
