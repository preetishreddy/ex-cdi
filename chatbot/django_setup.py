"""
Django Setup for Chatbot

Sets up Django and provides path constants.
"""

import os
import sys

# Paths
CHATBOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CHATBOT_DIR)

# Add project root to path so 'config' resolves to the main project's config/
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load .env from project root
from dotenv import load_dotenv
env_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(env_path)

# Setup Django — skip if already configured (e.g. when called from within Django)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
from django.apps import apps
if not apps.ready:
    django.setup()


def get_models():
    """Import and return all models."""
    from knowledge_base.models import (
        Decision, Meeting, JiraTicket, ConfluencePage,
        GitCommit, Employee
    )
    return {
        'Decision': Decision,
        'Meeting': Meeting,
        'JiraTicket': JiraTicket,
        'ConfluencePage': ConfluencePage,
        'GitCommit': GitCommit,
        'Employee': Employee,
    }