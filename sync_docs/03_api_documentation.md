title: "API Documentation"
space: "Onboarding Portal"
author: "Marcus Thompson"
created: "2026-01-15"
last_updated: "2026-01-29"
labels: ["api", "documentation", "endpoints", "backend"]
version: 4

# API Documentation

## Base URL

`/api/v1/`

## Authentication

All endpoints require JWT token in header:
```
Authorization: Bearer <token>
```

## Endpoints

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login/` | Login, returns JWT token |
| POST | `/auth/logout/` | Invalidate token |
| GET | `/auth/me/` | Get current user info |

### Employees

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/employees/` | List all employees |
| GET | `/employees/{id}/` | Get employee details |
| POST | `/employees/` | Create employee (admin) |
| PUT | `/employees/{id}/` | Update employee (admin) |

### Onboarding Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/` | List all task templates |
| GET | `/tasks/my/` | Get current user's tasks |
| POST | `/tasks/{id}/complete/` | Mark task as complete |

### Manager Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/manager/employees/` | List employees with progress |
| POST | `/manager/assign/` | Assign tasks to employee |

## Response Format

All responses follow this structure:
```json
{
  "success": true,
  "data": { },
  "message": "Success"
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 500 | Server error |
