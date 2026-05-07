"""
Retriever Module for Onboarding AI Chatbot

Fetches relevant data from the database based on classified intent.
Designed with abstraction for easy swapping in Phase 2/3.
"""

from .base import BaseRetriever, Document
from .sql_retriever import SQLRetriever

__all__ = [
    'BaseRetriever',
    'Document',
    'SQLRetriever',
]