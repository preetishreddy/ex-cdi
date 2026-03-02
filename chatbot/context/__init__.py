"""
Context Module for Onboarding AI Chatbot

Builds structured context from retrieved documents for LLM consumption.
Supports conversation history for multi-turn conversations.
"""

from .builder import ContextBuilder
from .templates import PromptTemplates, SYSTEM_PROMPT

__all__ = [
    'ContextBuilder',
    'PromptTemplates',
    'SYSTEM_PROMPT',
]
