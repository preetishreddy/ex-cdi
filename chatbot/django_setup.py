"""
Django Setup for Chatbot

Configures Django to allow importing models from outside the Django project.
"""

import os
import sys

# Get paths
CHATBOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CHATBOT_DIR)
DATABASE_DIR = os.path.join(PROJECT_ROOT, 'database')

# Add database directory to Python path
if DATABASE_DIR not in sys.path:
    sys.path.insert(0, DATABASE_DIR)

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(DATABASE_DIR, '.env')
load_dotenv(env_path)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
import django
django.setup()


def get_models():
    """
    Import and return all Django models.
    
    Returns:
        dict: Dictionary of model name -> model class
    """
    from knowledge_base.models import (
        Decision,
        Meeting,
        JiraTicket,
        ConfluencePage,
        GitCommit,
        Employee,
        Sprint,
        SprintTicket,
        EntityReference,
    )
    
    return {
        'Decision': Decision,
        'Meeting': Meeting,
        'JiraTicket': JiraTicket,
        'ConfluencePage': ConfluencePage,
        'GitCommit': GitCommit,
        'Employee': Employee,
        'Sprint': Sprint,
        'SprintTicket': SprintTicket,
        'EntityReference': EntityReference,
    }