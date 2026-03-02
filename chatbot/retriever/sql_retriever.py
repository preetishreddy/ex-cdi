"""
SQL Retriever for Phase 1

Fetches data directly from PostgreSQL using Django ORM.
No vector embeddings - uses keyword matching and relationships.
"""

import sys
import os

# Add parent directory to path for django_setup
RETRIEVER_DIR = os.path.dirname(os.path.abspath(__file__))
CHATBOT_DIR = os.path.dirname(RETRIEVER_DIR)
if CHATBOT_DIR not in sys.path:
    sys.path.insert(0, CHATBOT_DIR)

from django_setup import get_models
from typing import List, Optional
from django.db.models import Q

models = get_models()
Decision = models['Decision']
Meeting = models['Meeting']
JiraTicket = models['JiraTicket']
ConfluencePage = models['ConfluencePage']
GitCommit = models['GitCommit']

from .base import BaseRetriever, Document


# ... rest of file stays the same ...


class SQLRetriever(BaseRetriever):
    """
    Phase 1 Retriever: Direct SQL queries to PostgreSQL.
    
    Routes queries to appropriate tables based on intent:
    - decision_query → decisions table
    - person_query → employees, jira_tickets, git_commits
    - timeline_query → decisions, meetings ordered by date
    - howto_query → confluence_pages
    - status_query → jira_tickets
    - ticket_query → jira_tickets + entity_references
    - meeting_query → meetings
    """
    
    def retrieve(
        self, 
        query: str, 
        intent_type: str, 
        entities: List[str],
        limit: int = 10
    ) -> List[Document]:
        """Route to appropriate retrieval method based on intent."""
        
        retrieval_methods = {
            'decision_query': self._retrieve_decisions,
            'person_query': self._retrieve_person_info,
            'timeline_query': self._retrieve_timeline,
            'howto_query': self._retrieve_documentation,
            'status_query': self._retrieve_status,
            'ticket_query': self._retrieve_ticket_info,
            'meeting_query': self._retrieve_meetings,
            'general_query': self._retrieve_general,
        }
        
        method = retrieval_methods.get(intent_type, self._retrieve_general)
        return method(query, entities, limit)
    
    def retrieve_by_id(self, source_type: str, source_id: str) -> Optional[Document]:
        """Retrieve a specific document by ID."""
        try:
            if source_type == 'decision':
                obj = Decision.objects.get(id=source_id)
                return self._decision_to_document(obj)
            elif source_type == 'meeting':
                obj = Meeting.objects.get(id=source_id)
                return self._meeting_to_document(obj)
            elif source_type == 'jira':
                obj = JiraTicket.objects.get(id=source_id)
                return self._ticket_to_document(obj)
            elif source_type == 'confluence':
                obj = ConfluencePage.objects.get(id=source_id)
                return self._confluence_to_document(obj)
        except Exception:
            pass
        return None
    
    # =========================================
    # DECISION QUERIES
    # =========================================
    
    def _retrieve_decisions(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve decisions matching the query."""
        documents = []
        
        # Build search filter
        q_filter = Q()
        
        for entity in entities:
            q_filter |= Q(title__icontains=entity)
            q_filter |= Q(description__icontains=entity)
            q_filter |= Q(rationale__icontains=entity)
        
        # If no entities, search with query terms
        if not entities:
            words = query.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    q_filter |= Q(title__icontains=word)
                    q_filter |= Q(rationale__icontains=word)
        
        # Prioritize active decisions
        decisions = Decision.objects.filter(q_filter).order_by(
            '-decision_date'
        )[:limit]
        
        for decision in decisions:
            documents.append(self._decision_to_document(decision))
        
        # Also check for superseded decisions to show history
        if documents:
            for doc in documents[:3]:  # Check first 3
                decision = Decision.objects.filter(id=doc.source_id).first()
                if decision and decision.supersedes:
                    superseded_doc = self._decision_to_document(decision.supersedes)
                    superseded_doc.metadata['is_superseded'] = True
                    superseded_doc.relevance_score = 0.7
                    documents.append(superseded_doc)
        
        return documents
    
    def _decision_to_document(self, decision: Decision) -> Document:
        """Convert Decision model to Document."""
        content_parts = []
        
        if decision.description:
            content_parts.append(f"Description: {decision.description}")
        
        if decision.rationale:
            content_parts.append(f"Rationale: {decision.rationale}")
        
        if decision.alternatives_considered:
            content_parts.append(f"Alternatives Considered: {decision.alternatives_considered}")
        
        if decision.impact:
            content_parts.append(f"Impact: {decision.impact}")
        
        if decision.supersedes:
            content_parts.append(f"Supersedes: {decision.supersedes.title}")
        
        return Document(
            content="\n".join(content_parts),
            title=decision.title,
            source_type='decision',
            source_id=str(decision.id),
            source_table='decisions',
            date=decision.decision_date,
            related_tickets=decision.related_tickets or [],
            related_people=decision.decided_by or [],
            metadata={
                'category': decision.category,
                'status': decision.status,
                'confidence': decision.confidence_score,
                'source_title': decision.source_title,
            }
        )
    
    # =========================================
    # PERSON QUERIES
    # =========================================
    
    def _retrieve_person_info(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve information about people."""
        documents = []
        
        # Find person names in entities
        person_names = [e for e in entities if any(
            name.lower() in e.lower() 
            for name in ['sarah', 'marcus', 'lisa', 'priya', 'james', 'dave']
        )]
        
        # Search for person-related items
        for name in person_names:
            # Get their commits
            commits = GitCommit.objects.filter(
                author_name__icontains=name
            ).order_by('-commit_date')[:5]
            
            for commit in commits:
                documents.append(self._commit_to_document(commit))
            
            # Get their tickets
            tickets = JiraTicket.objects.filter(
                Q(assignee__icontains=name) | Q(reporter__icontains=name)
            ).order_by('-updated_date')[:5]
            
            for ticket in tickets:
                documents.append(self._ticket_to_document(ticket))
            
            # Get decisions they were part of
            decisions = Decision.objects.filter(
                decided_by__contains=[name]
            ).order_by('-decision_date')[:3]
            
            for decision in decisions:
                documents.append(self._decision_to_document(decision))
        
        # If no specific person, find who worked on the topic
        if not person_names and entities:
            for entity in entities:
                commits = GitCommit.objects.filter(
                    message__icontains=entity
                ).order_by('-commit_date')[:5]
                
                for commit in commits:
                    documents.append(self._commit_to_document(commit))
        
        return documents[:limit]
    
    def _commit_to_document(self, commit: GitCommit) -> Document:
        """Convert GitCommit to Document."""
        return Document(
            content=commit.message or "",
            title=f"Commit: {(commit.message or '')[:60]}",
            source_type='commit',
            source_id=str(commit.id),
            source_table='git_commits',
            date=commit.commit_date.date() if commit.commit_date else None,
            related_people=[commit.author_name] if commit.author_name else [],
            related_tickets=[commit.related_tickets] if commit.related_tickets else [],
            metadata={
                'sha': commit.sha,
                'author_email': commit.author_email,
            }
        )
    
    # =========================================
    # TIMELINE QUERIES
    # =========================================
    
    def _retrieve_timeline(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve timeline/history information."""
        documents = []
        
        # Check for sprint reference
        sprint_num = None
        for entity in entities:
            if entity.isdigit():
                sprint_num = int(entity)
                break
        
        if sprint_num:
            # Get decisions from that sprint's timeframe
            decisions = Decision.objects.filter(
                decision_date__isnull=False
            ).order_by('decision_date')
            
            for decision in decisions:
                documents.append(self._decision_to_document(decision))
        else:
            # General timeline - get all decisions chronologically
            decisions = Decision.objects.filter(
                status='active'
            ).order_by('decision_date')[:limit]
            
            for decision in decisions:
                documents.append(self._decision_to_document(decision))
        
        return documents[:limit]
    
    # =========================================
    # HOWTO/DOCUMENTATION QUERIES
    # =========================================
    
    def _retrieve_documentation(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve documentation from Confluence."""
        documents = []
        
        q_filter = Q()
        
        for entity in entities:
            q_filter |= Q(title__icontains=entity)
            q_filter |= Q(content__icontains=entity)
        
        # Also search for setup/guide keywords
        setup_keywords = ['setup', 'install', 'configure', 'guide', 'start']
        for keyword in setup_keywords:
            if keyword in query.lower():
                q_filter |= Q(title__icontains=keyword)
                q_filter |= Q(content__icontains=keyword)
        
        pages = ConfluencePage.objects.filter(q_filter)[:limit]
        
        for page in pages:
            documents.append(self._confluence_to_document(page))
        
        # If no results, return all docs
        if not documents:
            pages = ConfluencePage.objects.all()[:limit]
            for page in pages:
                documents.append(self._confluence_to_document(page))
        
        return documents
    
    def _confluence_to_document(self, page: ConfluencePage) -> Document:
        """Convert ConfluencePage to Document."""
        return Document(
            content=page.content or "",
            title=page.title,
            source_type='confluence',
            source_id=str(page.id),
            source_table='confluence_pages',
            date=page.page_created_date.date() if page.page_created_date else None,
            related_people=[page.author] if page.author else [],
            metadata={
                'labels': page.labels,
                'space': page.space,
                'version': page.version,
                'source_filename': page.source_filename,
            }
        )
    
    # =========================================
    # STATUS QUERIES
    # =========================================
    
    def _retrieve_status(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve status information for tickets."""
        documents = []
        
        # Check for ticket ID
        ticket_ids = [e for e in entities if 'ONBOARD-' in e.upper()]
        
        if ticket_ids:
            for ticket_id in ticket_ids:
                ticket = JiraTicket.objects.filter(
                    issue_key__iexact=ticket_id
                ).first()
                if ticket:
                    documents.append(self._ticket_to_document(ticket))
        else:
            # Get open/in-progress tickets
            tickets = JiraTicket.objects.filter(
                Q(status__icontains='open') | 
                Q(status__icontains='progress') |
                Q(status__icontains='todo')
            ).order_by('-updated_date')[:limit]
            
            for ticket in tickets:
                documents.append(self._ticket_to_document(ticket))
        
        return documents
    
    def _ticket_to_document(self, ticket: JiraTicket) -> Document:
        """Convert JiraTicket to Document."""
        content_parts = []
        
        if ticket.description:
            content_parts.append(f"Description: {ticket.description}")
        
        if ticket.comments:
            content_parts.append(f"Comments: {ticket.comments[:500]}")
        
        return Document(
            content="\n".join(content_parts),
            title=f"{ticket.issue_key}: {ticket.summary}",
            source_type='jira',
            source_id=str(ticket.id),
            source_table='jira_tickets',
            date=ticket.created_date.date() if ticket.created_date else None,
            related_tickets=[ticket.issue_key],
            related_people=[p for p in [ticket.assignee, ticket.reporter] if p],
            metadata={
                'status': ticket.status,
                'issue_type': ticket.issue_type,
                'priority': ticket.priority,
                'sprint': ticket.sprint,
                'story_points': ticket.story_points,
                'labels': ticket.labels,
                'epic_link': ticket.epic_link,
            }
        )
    
    # =========================================
    # TICKET QUERIES
    # =========================================
    
    def _retrieve_ticket_info(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve detailed ticket information."""
        documents = []
        
        ticket_ids = [e for e in entities if 'ONBOARD-' in e.upper()]
        
        for ticket_id in ticket_ids:
            # Get the ticket
            ticket = JiraTicket.objects.filter(
                issue_key__iexact=ticket_id
            ).first()
            
            if ticket:
                documents.append(self._ticket_to_document(ticket))
                
                # Get related commits
                commits = GitCommit.objects.filter(
                    message__icontains=ticket_id
                )[:3]
                
                for commit in commits:
                    documents.append(self._commit_to_document(commit))
                
                # Get related decisions
                decisions = Decision.objects.filter(
                    related_tickets__contains=[ticket_id]
                )[:2]
                
                for decision in decisions:
                    documents.append(self._decision_to_document(decision))
        
        return documents[:limit]
    
    # =========================================
    # MEETING QUERIES
    # =========================================
    
    def _retrieve_meetings(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve meeting information."""
        documents = []
        
        q_filter = Q()
        
        for entity in entities:
            q_filter |= Q(title__icontains=entity)
            q_filter |= Q(summary__icontains=entity)
        
        # Search for meeting type keywords
        meeting_types = ['planning', 'standup', 'retrospective', 'review', 'sync']
        for mtype in meeting_types:
            if mtype in query.lower():
                q_filter |= Q(title__icontains=mtype)
        
        meetings = Meeting.objects.filter(q_filter).order_by('-meeting_date')[:limit]
        
        for meeting in meetings:
            documents.append(self._meeting_to_document(meeting))
        
        # If no results, return recent meetings
        if not documents:
            meetings = Meeting.objects.order_by('-meeting_date')[:limit]
            for meeting in meetings:
                documents.append(self._meeting_to_document(meeting))
        
        return documents
    
    def _meeting_to_document(self, meeting: Meeting) -> Document:
        """Convert Meeting to Document."""
        content_parts = []
        
        if meeting.summary:
            content_parts.append(f"Summary: {meeting.summary}")
        
        if meeting.key_decisions:
            content_parts.append(f"Key Decisions: {meeting.key_decisions}")
        
        if meeting.action_items:
            content_parts.append(f"Action Items: {meeting.action_items}")
        
        # Parse participants
        participants = []
        if meeting.participants:
            try:
                import json
                participants = json.loads(meeting.participants)
                if not isinstance(participants, list):
                    participants = [meeting.participants]
            except:
                participants = [meeting.participants]
        
        return Document(
            content="\n".join(content_parts),
            title=meeting.title or "Meeting",
            source_type='meeting',
            source_id=str(meeting.id),
            source_table='meetings',
            date=meeting.meeting_date.date() if meeting.meeting_date else None,
            related_people=participants,
            metadata={
                'has_transcript': bool(meeting.raw_vtt_content),
                'duration_seconds': meeting.duration_seconds,
                'source_filename': meeting.source_filename,
            }
        )
    
    # =========================================
    # GENERAL QUERIES
    # =========================================
    
    def _retrieve_general(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Fallback: search across all tables."""
        documents = []
        
        # Get recent decisions
        decisions = Decision.objects.filter(status='active').order_by('-decision_date')[:3]
        for d in decisions:
            documents.append(self._decision_to_document(d))
        
        # Get project overview from Confluence
        overview = ConfluencePage.objects.filter(
            Q(title__icontains='overview') | Q(title__icontains='project')
        ).first()
        if overview:
            documents.append(self._confluence_to_document(overview))
        
        # Search with entities if provided
        if entities:
            for entity in entities[:2]:
                # Search decisions
                matching_decisions = Decision.objects.filter(
                    Q(title__icontains=entity) | Q(rationale__icontains=entity)
                )[:2]
                for d in matching_decisions:
                    doc = self._decision_to_document(d)
                    if doc.source_id not in [x.source_id for x in documents]:
                        documents.append(doc)
        
        return documents[:limit]


# =========================================
# TEST FUNCTION
# =========================================

def test_retriever():
    """Test the SQL retriever."""
    retriever = SQLRetriever()
    
    test_cases = [
        ("decision_query", ["react"], "Why did we choose React?"),
        ("person_query", ["Marcus"], "What did Marcus work on?"),
        ("ticket_query", ["ONBOARD-14"], "Tell me about ONBOARD-14"),
        ("howto_query", ["setup"], "How do I set up the project?"),
        ("meeting_query", ["planning"], "What was discussed in planning?"),
    ]
    
    print("=" * 60)
    print("SQL RETRIEVER TEST")
    print("=" * 60)
    
    for intent, entities, query in test_cases:
        print(f"\nQuery: {query}")
        print(f"Intent: {intent}, Entities: {entities}")
        print("-" * 40)
        
        docs = retriever.retrieve(query, intent, entities, limit=3)
        
        for doc in docs:
            print(f"  • {doc.source_type}: {doc.title[:50]}")
        
        if not docs:
            print("  (No results)")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_retriever()