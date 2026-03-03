# ex-cdi — Django Project

Backend of the ex-cdi project. Built with Django 5.2 and PostgreSQL.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Framework | Django 5.2 |
| REST API | Django REST Framework |
| API Docs | drf-spectacular (Swagger UI) |
| CORS | django-cors-headers |
| Database | PostgreSQL |
| DB Driver | psycopg2-binary |
| Env management | python-dotenv |
| AI / LLM | Bytez API (GPT-4o) |

---

## Project Structure

```
ex-cdi/
├── manage.py               ← Django CLI tool
├── .env                    ← local secrets (never commit)
├── .env.example            ← template for .env
├── .gitignore
├── requirements.txt
├── venv/                   ← virtual environment
├── config/                 ← project-level config
│   ├── settings.py         ← all project settings
│   ├── urls.py             ← root URL routing
│   ├── wsgi.py             ← production WSGI entry point
│   └── asgi.py             ← production ASGI entry point
├── api/                    ← REST API layer
│   ├── urls.py             ← all API route definitions
│   ├── views.py            ← all API views
│   ├── serializers.py      ← data serializers
│   └── ingestion.py        ← GitHub / Jira / Confluence ingest logic
├── knowledge_base/         ← database models
│   └── models.py           ← GitCommit, JiraTicket, Meeting, Decision, etc.
├── chatbot/                ← AI chatbot module
│   ├── main.py             ← main orchestrator (OnboardingChatbot)
│   ├── intent/             ← intent classification
│   ├── retriever/          ← SQL-based data retrieval
│   ├── context/            ← context building for LLM
│   └── llm/                ← Bytez/GPT-4o wrapper
├── frontend/               ← static frontend assets
│   └── static/
│       └── js/
│           └── solution_chat.js  ← AI chat panel
└── my_app/                 ← legacy app (kept for compatibility)
```

---

## Team Documentation

| Who | Read this |
|-----|-----------|
| Front-end developers | [FRONTEND_README.md](./FRONTEND_README.md) |
| Back-end developers | This file |

---

## Local Setup (Backend)

**1. Clone the repo and navigate into the project**
```bash
cd ex-cdi
```

**2. Create and activate the virtual environment**
```bash
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
cp .env.example .env
```
Open `.env` and fill in all values. See the Environment Variables section below.

**5. Apply database migrations**
```bash
python manage.py migrate
```

**6. Create a superuser (admin account)**
```bash
python manage.py createsuperuser
```

**7. Run the development server**
```bash
python manage.py runserver
```

Server runs at `http://127.0.0.1:8000`
Admin panel at `http://127.0.0.1:8000/admin`

---

## Environment Variables

All secrets live in `.env`. Never commit this file. Use `.env.example` as the template.

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key — keep this private | `django-insecure-...` |
| `DEBUG` | `True` in development, `False` in production | `True` |
| `DB_NAME` | PostgreSQL database name | `ex_cdi_db` |
| `DB_USER` | PostgreSQL username | `ex_cdi_user` |
| `DB_PASSWORD` | PostgreSQL password | `changeme` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `BYTEZ_API_KEY` | API key for Bytez (GPT-4o) — powers the AI chatbot | `your_key_here` |

---

## Common Commands

```bash
# Run development server
python manage.py runserver

# Create database migrations after changing models
python manage.py makemigrations

# Apply migrations to the database
python manage.py migrate

# Open Django shell (Python REPL with Django loaded)
python manage.py shell

# Run tests
python manage.py test

# Check for project issues
python manage.py check

# Collect static files (production only)
python manage.py collectstatic
```

---

## Adding a New App

```bash
python manage.py startapp app_name
```

Then register it in `config/settings.py` under `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    'app_name',
]
```

