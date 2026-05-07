title: "Local Development Setup Guide"
space: "Onboarding Portal"
author: "Dave Rossi"
created: "2026-01-10"
last_updated: "2026-01-25"
labels: ["setup", "development", "guide", "local"]
version: 3

# Local Development Setup Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Git

## Step 1: Clone Repository

```bash
git clone github.com/company/onboarding-portal.git
cd onboarding-portal
```

## Step 2: Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` file:
```
DB_NAME=onboarding_dev
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
SECRET_KEY=your-secret-key
DEBUG=True
```

Run migrations:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend runs at: `http://localhost:8000`

## Step 3: Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs at: `http://localhost:3000`

## Step 4: Verify Setup

1. Open `http://localhost:3000`
2. Login with superuser credentials
3. You should see the dashboard

## Common Issues

| Issue | Solution |
|-------|----------|
| DB connection error | Check PostgreSQL is running |
| Module not found | Activate virtual environment |
| CORS error | Backend must be running |

## Useful Commands

- Run tests: `python manage.py test`
- Create migration: `python manage.py makemigrations`
- Django shell: `python manage.py shell`
