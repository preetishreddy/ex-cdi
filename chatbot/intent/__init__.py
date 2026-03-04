"""
Intent Classification Module for Onboarding AI Chatbot

Provides intent classification and entity extraction from user queries.
"""

from .types import IntentType, ClassifiedIntent, INTENT_CONFIGS, ENTITY_PATTERNS, TECH_TERMS
from .classifier import IntentClassifier

__all__ = [
    'IntentType',
    'ClassifiedIntent',
    'IntentClassifier',
    'INTENT_CONFIGS',
    'ENTITY_PATTERNS',
    'TECH_TERMS',
]