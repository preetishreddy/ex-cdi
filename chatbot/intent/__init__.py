"""
Intent Classification Module for Onboarding AI Chatbot
"""

from .types import IntentType, ClassifiedIntent, INTENT_CONFIGS
from .classifier import IntentClassifier, classify_query

__all__ = [
    'IntentType',
    'ClassifiedIntent', 
    'INTENT_CONFIGS',
    'IntentClassifier',
    'classify_query',
]