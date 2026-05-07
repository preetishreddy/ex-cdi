"""
Prompt Templates for Onboarding AI Chatbot (Conversational Version)

Contains system prompts and response templates for different query types.
Supports multi-turn conversations with context carryover.
"""


SYSTEM_PROMPT = """You are an AI assistant for the Employee Onboarding Portal project.
You are having a CONVERSATION with a team member, so remember the context from previous messages.

Your role is to help new team members and existing staff understand:
- Project decisions and their rationale
- Who worked on what
- Technical architecture and setup
- Current status of work
- Meeting discussions and outcomes
- Sprint summaries and progress

IMPORTANT RULES:
1. Only answer based on the provided context
2. If information is marked as "superseded", mention that newer decisions exist
3. Always cite your sources (meeting name, ticket ID, etc.)
4. If you don't have enough information, say so clearly
5. Be concise but complete
6. When discussing decisions, explain the WHY (rationale) not just the WHAT
7. If the user refers to "it", "that", "they", use conversation history to understand

Current date context: January 2026
Project: Employee Onboarding Portal (Django + React)
"""


CONVERSATIONAL_SYSTEM_PROMPT = """You are an AI assistant for the Employee Onboarding Portal project.
You are having a MULTI-TURN CONVERSATION with a team member.

KEY BEHAVIOR:
- Remember what was discussed in previous messages
- When user says "it", "that", "they", "the decision", etc., refer to conversation history
- Maintain continuity and build on previous answers
- Be natural and conversational

Your role is to help understand:
- Project decisions and their rationale
- Who worked on what
- Technical architecture and setup
- Current status of work
- Meeting discussions and outcomes
- Sprint summaries and progress

RULES:
1. Only answer based on the provided context
2. Use conversation history to resolve references
3. Cite your sources (meeting name, ticket ID, etc.)
4. If you don't have enough information, say so clearly
5. Be concise but complete
"""


class PromptTemplates:
    """Templates for different query types with conversation support."""
    
    @staticmethod
    def decision_query(context: str, query: str) -> str:
        return f"""{SYSTEM_PROMPT}

The user is asking about a DECISION. Focus on:
- What was decided
- WHY it was decided (rationale)
- What alternatives were considered
- Who was involved
- If this supersedes a previous decision, explain the change

CONTEXT:
{context}

USER QUESTION: {query}

Provide a clear, helpful answer explaining the decision and its reasoning."""

    @staticmethod
    def person_query(context: str, query: str) -> str:
        return f"""{SYSTEM_PROMPT}

The user is asking about a PERSON or who worked on something. Focus on:
- What work they did (commits, tickets)
- What decisions they were involved in
- Their role in the project

CONTEXT:
{context}

USER QUESTION: {query}

Provide a summary of the person's contributions and involvement."""

    @staticmethod
    def timeline_query(context: str, query: str) -> str:
        return f"""{SYSTEM_PROMPT}

The user is asking about TIMELINE or history. Focus on:
- Chronological order of events
- Key milestones and decisions
- How things evolved over time

CONTEXT:
{context}

USER QUESTION: {query}

Provide a chronological summary of relevant events."""

    @staticmethod
    def howto_query(context: str, query: str) -> str:
        return f"""{SYSTEM_PROMPT}

The user is asking HOW TO do something. Focus on:
- Step-by-step instructions
- Prerequisites
- Common issues and solutions

CONTEXT:
{context}

USER QUESTION: {query}

Provide clear, actionable instructions."""

    @staticmethod
    def status_query(context: str, query: str) -> str:
        return f"""{SYSTEM_PROMPT}

The user is asking about STATUS. Focus on:
- Current state (open, in progress, done)
- Who is assigned
- Any blockers or issues
- Recent updates

CONTEXT:
{context}

USER QUESTION: {query}

Provide a clear status update."""

    @staticmethod
    def ticket_query(context: str, query: str) -> str:
        return f"""{SYSTEM_PROMPT}

The user is asking about a specific TICKET. Focus on:
- What the ticket is about
- Current status
- Who is working on it
- Related commits and decisions
- Any discussions in comments

CONTEXT:
{context}

USER QUESTION: {query}

Provide comprehensive information about the ticket."""

    @staticmethod
    def meeting_query(context: str, query: str) -> str:
        return f"""{SYSTEM_PROMPT}

The user is asking about a MEETING. Focus on:
- What was discussed
- Key decisions made
- Action items assigned
- Who attended

CONTEXT:
{context}

USER QUESTION: {query}

Summarize the meeting and its outcomes."""

    @staticmethod
    def sprint_summary_query(context: str, query: str) -> str:
        """NEW: Template for sprint summary queries."""
        return f"""{SYSTEM_PROMPT}

The user is asking for a SPRINT SUMMARY. Provide a comprehensive overview including:

1. SPRINT OVERVIEW
   - Sprint goal and duration
   - Overall progress and completion rate

2. KEY ACCOMPLISHMENTS
   - Major tickets completed
   - Important features delivered

3. DECISIONS MADE
   - Technical decisions during the sprint
   - Rationale for key choices

4. TEAM CONTRIBUTIONS
   - Who worked on what
   - Notable individual contributions

5. CHALLENGES & BLOCKERS (if any)
   - Issues encountered
   - How they were resolved

6. MEETINGS & DISCUSSIONS
   - Important meetings held
   - Key discussion points

Format your response in a clear, structured way that gives the user a complete picture of what happened during the sprint.

CONTEXT:
{context}

USER QUESTION: {query}

Provide a comprehensive sprint summary:"""

    @staticmethod
    def general_query(context: str, query: str) -> str:
        return f"""{SYSTEM_PROMPT}

The user has a general question. Provide helpful information based on the context.

CONTEXT:
{context}

USER QUESTION: {query}

Provide a helpful, informative answer."""

    @staticmethod
    def conversational_query(context: str, query: str, history: str = "") -> str:
        """Template for multi-turn conversations with history."""
        history_section = f"\nCONVERSATION HISTORY:\n{history}\n" if history else ""
        
        return f"""{CONVERSATIONAL_SYSTEM_PROMPT}
{history_section}
CONTEXT FROM DATABASE:
{context}

CURRENT QUESTION: {query}

Provide a helpful answer that takes into account the conversation history:"""

    @classmethod
    def get_template(cls, intent_type: str) -> callable:
        """Get the appropriate template for an intent type."""
        templates = {
            'decision_query': cls.decision_query,
            'person_query': cls.person_query,
            'timeline_query': cls.timeline_query,
            'howto_query': cls.howto_query,
            'status_query': cls.status_query,
            'ticket_query': cls.ticket_query,
            'meeting_query': cls.meeting_query,
            'sprint_summary_query': cls.sprint_summary_query,  # NEW
            'general_query': cls.general_query,
        }
        return templates.get(intent_type, cls.general_query)
