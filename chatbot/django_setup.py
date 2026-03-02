"""
Django Setup for Chatbot

Sets up Django and provides path constants.
"""

import os
import sys

# Paths
CHATBOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CHATBOT_DIR)
DATABASE_DIR = os.path.join(PROJECT_ROOT, 'database')

# Add database to path BEFORE importing Django
if DATABASE_DIR not in sys.path:
    sys.path.insert(0, DATABASE_DIR)

# Load .env file from database folder
from dotenv import load_dotenv
env_path = os.path.join(DATABASE_DIR, '.env')
load_dotenv(env_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
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