"""
Intent Types for Onboarding AI Chatbot
"""

from enum import Enum
from dataclasses import dataclass
from typing import List


class IntentType(Enum):
    DECISION_QUERY = "decision_query"
    PERSON_QUERY = "person_query"
    TIMELINE_QUERY = "timeline_query"
    HOWTO_QUERY = "howto_query"
    STATUS_QUERY = "status_query"
    TICKET_QUERY = "ticket_query"
    MEETING_QUERY = "meeting_query"
    GENERAL_QUERY = "general_query"


@dataclass
class IntentConfig:
    intent_type: IntentType
    keywords: List[str]
    tables: List[str]
    description: str
    example_queries: List[str]


INTENT_CONFIGS = {
    IntentType.DECISION_QUERY: IntentConfig(
        intent_type=IntentType.DECISION_QUERY,
        keywords=['why', 'decision', 'decided', 'chose', 'choose', 'switch', 'switched', 'reason', 'rationale', 'alternatives'],
        tables=['decisions', 'meetings'],
        description="Questions about why decisions were made",
        example_queries=["Why did we choose React?", "Why did we switch to Tailwind?"]
    ),
    IntentType.PERSON_QUERY: IntentConfig(
        intent_type=IntentType.PERSON_QUERY,
        keywords=['who', 'worked', 'working', 'assigned', 'responsible', 'owner', 'author'],
        tables=['employees', 'jira_tickets', 'git_commits', 'decisions'],
        description="Questions about people and assignments",
        example_queries=["Who worked on authentication?", "What is Marcus working on?"]
    ),
    IntentType.TIMELINE_QUERY: IntentConfig(
        intent_type=IntentType.TIMELINE_QUERY,
        keywords=['when', 'timeline', 'history', 'sprint', 'first', 'last', 'before', 'after'],
        tables=['decisions', 'sprints', 'jira_tickets', 'meetings'],
        description="Questions about project timeline",
        example_queries=["What happened in Sprint 1?", "When was authentication implemented?"]
    ),
    IntentType.HOWTO_QUERY: IntentConfig(
        intent_type=IntentType.HOWTO_QUERY,
        keywords=['how', 'setup', 'set up', 'configure', 'install', 'run', 'guide', 'steps'],
        tables=['confluence_pages'],
        description="Questions about how to do something",
        example_queries=["How do I set up the project locally?", "How to run tests?"]
    ),
    IntentType.STATUS_QUERY: IntentConfig(
        intent_type=IntentType.STATUS_QUERY,
        keywords=['status', 'progress', 'done', 'complete', 'pending', 'blocked', 'open', 'closed'],
        tables=['jira_tickets', 'sprints'],
        description="Questions about current status",
        example_queries=["What's the status of ONBOARD-15?", "What tickets are still open?"]
    ),
    IntentType.TICKET_QUERY: IntentConfig(
        intent_type=IntentType.TICKET_QUERY,
        keywords=['ticket', 'issue', 'jira', 'onboard-', 'task', 'bug'],
        tables=['jira_tickets', 'git_commits', 'entity_references'],
        description="Questions about specific tickets",
        example_queries=["Tell me about ONBOARD-14", "What commits are linked to ONBOARD-15?"]
    ),
    IntentType.MEETING_QUERY: IntentConfig(
        intent_type=IntentType.MEETING_QUERY,
        keywords=['meeting', 'discussed', 'discussion', 'standup', 'planning', 'retrospective'],
        tables=['meetings'],
        description="Questions about meetings",
        example_queries=["What was discussed in Sprint 1 planning?", "Summarize the last standup"]
    ),
    IntentType.GENERAL_QUERY: IntentConfig(
        intent_type=IntentType.GENERAL_QUERY,
        keywords=[],
        tables=['decisions', 'meetings', 'jira_tickets', 'confluence_pages'],
        description="General questions",
        example_queries=["Tell me about the project", "What should I know as a new joiner?"]
    ),
}


@dataclass
class ClassifiedIntent:
    intent_type: IntentType
    confidence: float
    entities: List[str]
    original_query: str
    
    @property
    def tables(self) -> List[str]:
        return INTENT_CONFIGS[self.intent_type].tables
    
    def __str__(self):
        return f"Intent({self.intent_type.value}, conf={self.confidence:.2f}, entities={self.entities})"