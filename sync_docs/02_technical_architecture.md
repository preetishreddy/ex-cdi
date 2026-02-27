title: "Technical Architecture"
space: "Onboarding Portal"
author: "Marcus Thompson"
created: "2026-01-08"
last_updated: "2026-01-28"
labels: ["architecture", "technical", "backend", "frontend", "infrastructure"]
version: 5

# Technical Architecture

## Overview

The Employee Onboarding Portal uses a standard three-tier architecture with a React frontend, Django backend, and PostgreSQL database.

## Architecture Diagram

```
[React Frontend] → [Django REST API] → [PostgreSQL]
       ↓                   ↓
   [Tailwind]         [SQLAlchemy]
```

## Backend

- **Framework:** Django 4.2 with Django REST Framework
- **ORM:** Django ORM for simple queries, SQLAlchemy Core for complex queries
- **Auth:** JWT tokens with 24-hour expiry
- **Structure:** Service layer pattern for business logic

## Frontend

- **Framework:** React 18
- **Styling:** Tailwind CSS
- **State:** React Context for global state
- **API:** Axios for HTTP requests

## Database

- **Engine:** PostgreSQL 16
- **Key Tables:** employees, onboarding_tasks, task_assignments, departments

## Deployment

- **Platform:** AWS
- **Compute:** ECS Fargate (serverless containers)
- **Database:** RDS PostgreSQL
- **CI/CD:** GitHub Actions

## Key Decisions

| Decision | Reason |
|----------|--------|
| Tailwind over Material UI | More flexibility for custom designs |
| SQLAlchemy addition | Better support for complex queries |
| ECS Fargate | No server management needed |
| JWT auth | Stateless, scalable authentication |

## API Base URL

- Local: `http://localhost:8000/api/v1/`
- Staging: `https://staging.onboarding.internal/api/v1/`
