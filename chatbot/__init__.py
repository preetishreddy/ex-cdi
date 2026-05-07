"""
Onboarding AI Chatbot (Conversational)

A conversational assistant for the Employee Onboarding Portal project.
Helps new joiners and team members understand project decisions,
architecture, and history.

Features:
- Multi-turn conversations with memory
- Follow-up questions support
- Reference resolution ("it", "that", "they")
- Intent classification
- Database retrieval
- GPT-4o powered responses

Usage:
    from chatbot import OnboardingChatbot
    
    bot = OnboardingChatbot()
    
    # First question
    response = bot.chat("Why did we choose React?")
    print(response)
    
    # Follow-up (bot remembers context)
    response = bot.chat("Who made that decision?")
    print(response)
    
    # Clear history to start fresh
    bot.clear_history()
"""

from .main import OnboardingChatbot, ChatResponse, ConversationHistory, Message

__version__ = "2.0.0"

__all__ = [
    'OnboardingChatbot',
    'ChatResponse',
    'ConversationHistory',
    'Message',
]
