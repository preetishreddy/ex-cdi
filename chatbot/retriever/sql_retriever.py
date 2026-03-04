"""
SQL Retriever for Phase 1 (v3)

Fixes applied:
1. Better person query handling
2. List all X queries support
3. Role/topic to person mapping
4. Confluence page listing
"""

import sys
import os
import re

RETRIEVER_DIR = os.path.dirname(os.path.abspath(__file__))
CHATBOT_DIR = os.path.dirname(RETRIEVER_DIR)
if CHATBOT_DIR not in sys.path:
    sys.path.insert(0, CHATBOT_DIR)

from django_setup import get_models
from typing import List, Optional
from django.db.models import Q, Count

models = get_models()
Decision = models['Decision']
Meeting = models['Meeting']
JiraTicket = models['JiraTicket']
ConfluencePage = models['ConfluencePage']
GitCommit = models['GitCommit']
Sprint = models['Sprint']
SprintTicket = models['SprintTicket']

from .base import BaseRetriever, Document


class SQLRetriever(BaseRetriever):
    """SQL Retriever with improved person and list queries."""
    
    # Known person names for better matching
    KNOWN_PERSONS = {
        'sarah': 'Sarah Chen',
        'sarah chen': 'Sarah Chen',
        'marcus': 'Marcus Thompson',
        'marcus thompson': 'Marcus Thompson',
        'lisa': 'Lisa Park',
        'lisa park': 'Lisa Park',
        'priya': 'Priya Sharma',
        'priya sharma': 'Priya Sharma',
        'james': "James O'Brien",
        "james o'brien": "James O'Brien",
        'dave': 'Dave Rossi',
        'dave rossi': 'Dave Rossi',
    }
    
    def retrieve(
        self, 
        query: str, 
        intent_type: str, 
        entities: List[str],
        limit: int = 10
    ) -> List[Document]:
        """Route to appropriate retrieval method."""
        
        retrieval_methods = {
            'decision_query': self._retrieve_decisions,
            'person_query': self._retrieve_person_info,
            'timeline_query': self._retrieve_timeline,
            'howto_query': self._retrieve_documentation,
            'status_query': self._retrieve_status,
            'ticket_query': self._retrieve_ticket_info,
            'meeting_query': self._retrieve_meetings,
            'sprint_summary_query': self._retrieve_sprint_summary,
            'general_query': self._retrieve_general,
        }
        
        # Check for "list all" type queries
        if self._is_list_query(query):
            return self._retrieve_list(query, entities, limit)
        
        method = retrieval_methods.get(intent_type, self._retrieve_general)
        return method(query, entities, limit)
    
    def _is_list_query(self, query: str) -> bool:
        """Check if query is asking for a list of items."""
        query_lower = query.lower()
        list_patterns = [
            'list all', 'show all', 'what are all', 'all the',
            'available', 'what pages', 'what documents', 'what decisions',
            'what meetings', 'what tickets'
        ]
        return any(pattern in query_lower for pattern in list_patterns)
    
    def _retrieve_list(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Handle list queries."""
        query_lower = query.lower()
        documents = []
        
        if 'confluence' in query_lower or 'page' in query_lower or 'document' in query_lower:
            # List all Confluence pages
            pages = ConfluencePage.objects.all()[:limit]
            for page in pages:
                documents.append(self._confluence_to_document(page))
            
            # Add summary document
            if documents:
                summary = Document(
                    content=f"Found {len(documents)} Confluence pages:\n" + 
                            "\n".join([f"- {d.title}" for d in documents]),
                    title=f"Confluence Pages Summary ({len(documents)} pages)",
                    source_type='summary',
                    source_id='',
                    source_table='confluence_pages',
                    date=None,
                    related_tickets=[],
                    related_people=[],
                    metadata={'count': len(documents)}
                )
                documents.insert(0, summary)
        
        elif 'decision' in query_lower:
            decisions = Decision.objects.filter(status='active').order_by('-decision_date')[:limit]
            for d in decisions:
                documents.append(self._decision_to_document(d))
            
            if documents:
                summary = Document(
                    content=f"Found {len(documents)} active decisions:\n" + 
                            "\n".join([f"- {d.title}" for d in documents]),
                    title=f"Decisions Summary ({len(documents)} decisions)",
                    source_type='summary',
                    source_id='',
                    source_table='decisions',
                    date=None,
                    related_tickets=[],
                    related_people=[],
                    metadata={'count': len(documents)}
                )
                documents.insert(0, summary)
        
        elif 'meeting' in query_lower:
            meetings = Meeting.objects.all().order_by('-meeting_date')[:limit]
            for m in meetings:
                documents.append(self._meeting_to_document(m))
            
            if documents:
                summary = Document(
                    content=f"Found {len(documents)} meetings:\n" + 
                            "\n".join([f"- {d.title} ({d.date})" for d in documents]),
                    title=f"Meetings Summary ({len(documents)} meetings)",
                    source_type='summary',
                    source_id='',
                    source_table='meetings',
                    date=None,
                    related_tickets=[],
                    related_people=[],
                    metadata={'count': len(documents)}
                )
                documents.insert(0, summary)
        
        elif 'ticket' in query_lower:
            tickets = JiraTicket.objects.all().order_by('-created_date')[:limit]
            for t in tickets:
                documents.append(self._ticket_to_document(t))
        
        return documents
    
    def _normalize_person_name(self, name: str) -> Optional[str]:
        """Normalize person name to full name."""
        if not name:
            return None
        name_lower = name.lower().strip()
        return self.KNOWN_PERSONS.get(name_lower, name)
    
    def _extract_sprint_number(self, query: str, entities: List[str]) -> Optional[int]:
        """Extract sprint number from query or entities."""
        for entity in entities:
            if isinstance(entity, str) and entity.isdigit():
                return int(entity)
            match = re.search(r'(\d+)', str(entity))
            if match:
                return int(match.group(1))
        
        match = re.search(r'sprint\s*(\d+)', query.lower())
        if match:
            return int(match.group(1))
        
        return None
    
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
    # PERSON QUERIES (IMPROVED)
    # =========================================
    
    def _retrieve_person_info(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """
        Retrieve information about people.
        
        Improved to:
        1. Better name matching
        2. Search by role/topic if no name found
        3. Aggregate commits, tickets, and decisions
        """
        documents = []
        query_lower = query.lower()
        
        # Find person names in entities
        person_names = []
        for entity in entities:
            if isinstance(entity, str):
                normalized = self._normalize_person_name(entity)
                if normalized and normalized not in person_names:
                    person_names.append(normalized)
        
        # Also check query directly for person names
        for short_name, full_name in self.KNOWN_PERSONS.items():
            if short_name in query_lower and full_name not in person_names:
                person_names.append(full_name)
        
        self._log(f"Person names found: {person_names}")
        
        if person_names:
            for name in person_names:
                # Get their commits
                commits = GitCommit.objects.filter(
                    author_name__icontains=name.split()[0]  # Search by first name
                ).order_by('-commit_date')[:5]
                
                for commit in commits:
                    documents.append(self._commit_to_document(commit))
                
                # Get their tickets (assigned or reported)
                name_parts = name.split()
                first_name = name_parts[0] if name_parts else name
                
                tickets = JiraTicket.objects.filter(
                    Q(assignee__icontains=first_name) | Q(reporter__icontains=first_name)
                ).order_by('-updated_date')[:5]
                
                for ticket in tickets:
                    documents.append(self._ticket_to_document(ticket))
                
                # Get decisions they were involved in
                decisions = Decision.objects.filter(
                    Q(decided_by__icontains=first_name)
                ).order_by('-decision_date')[:3]
                
                for decision in decisions:
                    documents.append(self._decision_to_document(decision))
                
                # Create a person summary document if we found data
                if documents:
                    summary = self._create_person_summary(name, documents)
                    documents.insert(0, summary)
        
        # If no specific person but topic mentioned (e.g., "frontend", "backend")
        if not documents:
            topic_person_map = {
                'frontend': 'Lisa',
                'front-end': 'Lisa',
                'ui': 'Lisa',
                'react': 'Lisa',
                'backend': 'Marcus',
                'back-end': 'Marcus',
                'api': 'Marcus',
                'auth': 'Marcus',
                'database': 'Sarah',
                'schema': 'Sarah',
                'devops': 'Dave',
                'ci/cd': 'Dave',
            }
            
            for topic, person_first in topic_person_map.items():
                if topic in query_lower:
                    # Recursively call with the person name
                    return self._retrieve_person_info(query, [person_first], limit)
        
        return documents[:limit]
    
    def _create_person_summary(self, name: str, documents: List[Document]) -> Document:
        """Create a summary document for a person."""
        commits = [d for d in documents if d.source_type == 'commit']
        tickets = [d for d in documents if d.source_type == 'jira']
        decisions = [d for d in documents if d.source_type == 'decision']
        
        content = f"""SUMMARY FOR {name.upper()}

Commits: {len(commits)}
Tickets: {len(tickets)}
Decisions involved: {len(decisions)}

"""
        if commits:
            content += "Recent Commits:\n"
            for c in commits[:3]:
                content += f"  - {c.title}\n"
            content += "\n"
        
        if tickets:
            content += "Assigned Tickets:\n"
            for t in tickets[:3]:
                content += f"  - {t.title}\n"
            content += "\n"
        
        if decisions:
            content += "Decisions Involved:\n"
            for d in decisions[:3]:
                content += f"  - {d.title}\n"
        
        return Document(
            content=content,
            title=f"{name} - Work Summary",
            source_type='person_summary',
            source_id='',
            source_table='',
            date=None,
            related_tickets=[t.related_tickets[0] for t in tickets if t.related_tickets],
            related_people=[name],
            relevance_score=1.0,
            metadata={
                'person_name': name,
                'commit_count': len(commits),
                'ticket_count': len(tickets),
                'decision_count': len(decisions),
            }
        )
    
    def _log(self, message: str):
        """Debug logging."""
        # Uncomment for debugging:
        # print(f"[Retriever] {message}")
        pass
    
    # =========================================
    # SPRINT SUMMARY QUERY
    # =========================================
    
    def _retrieve_sprint_summary(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve sprint summary."""
        documents = []
        
        sprint_num = self._extract_sprint_number(query, entities)
        
        if not sprint_num:
            return self._retrieve_all_sprints_overview(limit)
        
        try:
            sprint = Sprint.objects.get(sprint_number=sprint_num)
        except Sprint.DoesNotExist:
            return [Document(
                content=f"Sprint {sprint_num} not found.",
                title=f"Sprint {sprint_num} Not Found",
                source_type='error',
                source_id='',
                source_table='sprints',
                date=None,
                related_tickets=[],
                related_people=[],
                metadata={'error': True}
            )]
        
        sprint_data = self._aggregate_sprint_data(sprint)
        documents.append(self._sprint_data_to_document(sprint, sprint_data))
        
        return documents
    
    def _aggregate_sprint_data(self, sprint: Sprint) -> dict:
        """Aggregate all data for a sprint."""
        start_date = sprint.start_date
        end_date = sprint.end_date
        
        sprint_ticket_ids = SprintTicket.objects.filter(
            sprint=sprint
        ).values_list('ticket_id', flat=True)
        
        tickets = JiraTicket.objects.filter(id__in=sprint_ticket_ids)
        
        tickets_by_status = {}
        for ticket in tickets:
            status = ticket.status or 'Unknown'
            if status not in tickets_by_status:
                tickets_by_status[status] = []
            tickets_by_status[status].append(ticket)
        
        decisions = Decision.objects.filter(
            decision_date__gte=start_date,
            decision_date__lte=end_date
        ).order_by('decision_date')
        
        meetings = Meeting.objects.filter(
            meeting_date__gte=start_date,
            meeting_date__lte=end_date
        ).order_by('meeting_date')
        
        commits = GitCommit.objects.filter(
            commit_date__date__gte=start_date,
            commit_date__date__lte=end_date
        ).order_by('commit_date')
        
        contributors = set()
        for ticket in tickets:
            if ticket.assignee:
                contributors.add(ticket.assignee)
            if ticket.reporter:
                contributors.add(ticket.reporter)
        for commit in commits:
            if commit.author_name:
                contributors.add(commit.author_name)
        
        return {
            'tickets': list(tickets),
            'tickets_by_status': tickets_by_status,
            'decisions': list(decisions),
            'meetings': list(meetings),
            'commits': list(commits),
            'contributors': list(contributors),
            'stats': {
                'total_tickets': tickets.count(),
                'completed_tickets': tickets.filter(status__icontains='done').count(),
                'in_progress_tickets': tickets.filter(
                    Q(status__icontains='progress') | Q(status__icontains='review')
                ).count(),
                'open_tickets': tickets.filter(
                    Q(status__icontains='open') | Q(status__icontains='todo')
                ).count(),
                'total_decisions': decisions.count(),
                'total_meetings': meetings.count(),
                'total_commits': commits.count(),
                'total_contributors': len(contributors),
            }
        }
    
    def _sprint_data_to_document(self, sprint: Sprint, data: dict) -> Document:
        """Convert sprint data to Document."""
        content_parts = []
        stats = data['stats']
        
        content_parts.append(f"SPRINT {sprint.sprint_number}: {sprint.name}")
        content_parts.append(f"Duration: {sprint.start_date} to {sprint.end_date}")
        if sprint.goal:
            content_parts.append(f"Goal: {sprint.goal}")
        content_parts.append("")
        
        content_parts.append("STATISTICS:")
        content_parts.append(f"- Total Tickets: {stats['total_tickets']}")
        content_parts.append(f"- Completed: {stats['completed_tickets']}")
        content_parts.append(f"- In Progress: {stats['in_progress_tickets']}")
        content_parts.append(f"- Open/To Do: {stats['open_tickets']}")
        content_parts.append(f"- Decisions Made: {stats['total_decisions']}")
        content_parts.append(f"- Meetings Held: {stats['total_meetings']}")
        content_parts.append(f"- Commits: {stats['total_commits']}")
        content_parts.append(f"- Contributors: {stats['total_contributors']}")
        content_parts.append("")
        
        content_parts.append("TICKETS BY STATUS:")
        for status, tickets in data['tickets_by_status'].items():
            content_parts.append(f"  {status}:")
            for ticket in tickets[:5]:
                assignee = f" ({ticket.assignee})" if ticket.assignee else ""
                content_parts.append(f"    - {ticket.issue_key}: {ticket.summary}{assignee}")
            if len(tickets) > 5:
                content_parts.append(f"    ... and {len(tickets) - 5} more")
        content_parts.append("")
        
        if data['decisions']:
            content_parts.append("KEY DECISIONS:")
            for decision in data['decisions'][:5]:
                content_parts.append(f"  - {decision.title}")
            content_parts.append("")
        
        if data['meetings']:
            content_parts.append("MEETINGS:")
            for meeting in data['meetings']:
                content_parts.append(f"  - {meeting.title} ({meeting.meeting_date})")
            content_parts.append("")
        
        if data['contributors']:
            content_parts.append("CONTRIBUTORS:")
            for contributor in list(data['contributors'])[:10]:
                content_parts.append(f"  - {contributor}")
        
        related_tickets = [t.issue_key for t in data['tickets']]
        
        return Document(
            content="\n".join(content_parts),
            title=f"Sprint {sprint.sprint_number} Summary: {sprint.name}",
            source_type='sprint_summary',
            source_id=str(sprint.id),
            source_table='sprints',
            date=sprint.start_date,
            related_tickets=related_tickets,
            related_people=list(data['contributors']),
            relevance_score=1.0,
            metadata={'sprint_number': sprint.sprint_number, 'stats': stats}
        )
    
    def _retrieve_all_sprints_overview(self, limit: int) -> List[Document]:
        """Retrieve all sprints overview."""
        documents = []
        sprints = Sprint.objects.all().order_by('sprint_number')[:limit]
        for sprint in sprints:
            data = self._aggregate_sprint_data(sprint)
            documents.append(self._sprint_data_to_document(sprint, data))
        return documents
    
    # =========================================
    # STATUS QUERIES
    # =========================================
    
    def _retrieve_status(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve status information."""
        documents = []
        
        ticket_ids = [e for e in entities if isinstance(e, str) and 'ONBOARD-' in e.upper()]
        
        if ticket_ids:
            for ticket_id in ticket_ids:
                ticket = JiraTicket.objects.filter(issue_key__iexact=ticket_id).first()
                if ticket:
                    documents.append(self._ticket_to_document(ticket))
            return documents
        
        sprint_num = self._extract_sprint_number(query, entities)
        
        if sprint_num:
            try:
                sprint = Sprint.objects.get(sprint_number=sprint_num)
                sprint_ticket_ids = SprintTicket.objects.filter(
                    sprint=sprint
                ).values_list('ticket_id', flat=True)
                
                tickets = JiraTicket.objects.filter(id__in=sprint_ticket_ids)
                
                if not tickets.exists():
                    return [Document(
                        content=f"No tickets found for Sprint {sprint_num}.",
                        title=f"Sprint {sprint_num} - No Tickets",
                        source_type='error',
                        source_id='',
                        source_table='sprints',
                        date=None,
                        related_tickets=[],
                        related_people=[],
                        metadata={'error': True}
                    )]
                
                summary = self._create_sprint_status_summary(sprint, tickets)
                documents.append(summary)
                
                for ticket in tickets[:limit-1]:
                    documents.append(self._ticket_to_document(ticket))
                
                return documents
                
            except Sprint.DoesNotExist:
                return [Document(
                    content=f"Sprint {sprint_num} not found.",
                    title=f"Sprint {sprint_num} Not Found",
                    source_type='error',
                    source_id='',
                    source_table='sprints',
                    date=None,
                    related_tickets=[],
                    related_people=[],
                    metadata={'error': True}
                )]
        
        # Default: get non-done tickets
        tickets = JiraTicket.objects.exclude(
            status__icontains='done'
        ).order_by('-updated_date')[:limit]
        
        if not tickets.exists():
            tickets = JiraTicket.objects.all().order_by('-updated_date')[:limit]
        
        for ticket in tickets:
            documents.append(self._ticket_to_document(ticket))
        
        return documents
    
    def _create_sprint_status_summary(self, sprint: Sprint, tickets) -> Document:
        """Create sprint status summary."""
        total = tickets.count()
        done = tickets.filter(status__icontains='done').count()
        in_progress = tickets.filter(
            Q(status__icontains='progress') | Q(status__icontains='review')
        ).count()
        open_count = tickets.filter(
            Q(status__icontains='open') | Q(status__icontains='todo')
        ).count()
        blocked = tickets.filter(status__icontains='block').count()
        
        completion_pct = (done / total * 100) if total > 0 else 0
        
        if completion_pct == 100:
            status_label = "✅ COMPLETED"
        elif completion_pct >= 75:
            status_label = "🟢 ON TRACK"
        elif completion_pct >= 50:
            status_label = "🟡 IN PROGRESS"
        else:
            status_label = "🔴 NEEDS ATTENTION"
        
        content = f"""SPRINT {sprint.sprint_number} STATUS: {status_label}

Sprint: {sprint.name}
Duration: {sprint.start_date} to {sprint.end_date}

TICKET BREAKDOWN:
- Total: {total}
- ✅ Done: {done}
- 🔄 In Progress: {in_progress}
- 📋 Open/To Do: {open_count}
- 🚫 Blocked: {blocked}

PROGRESS: {done}/{total} ({completion_pct:.0f}%)
"""
        
        if completion_pct == 100:
            content += f"\n🎉 All Sprint {sprint.sprint_number} tickets completed!"
        
        return Document(
            content=content,
            title=f"Sprint {sprint.sprint_number} Status: {status_label}",
            source_type='sprint_status',
            source_id=str(sprint.id),
            source_table='sprints',
            date=sprint.start_date,
            related_tickets=[],
            related_people=[],
            relevance_score=1.0,
            metadata={'sprint_number': sprint.sprint_number, 'completion': completion_pct}
        )
    
    # =========================================
    # DECISION QUERIES
    # =========================================
    
    def _retrieve_decisions(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve decisions."""
        documents = []
        
        q_filter = Q()
        
        for entity in entities:
            if isinstance(entity, str):
                q_filter |= Q(title__icontains=entity)
                q_filter |= Q(description__icontains=entity)
                q_filter |= Q(rationale__icontains=entity)
                q_filter |= Q(alternatives_considered__icontains=entity)
        
        if not entities:
            words = query.lower().split()
            for word in words:
                if len(word) > 3:
                    q_filter |= Q(title__icontains=word)
                    q_filter |= Q(rationale__icontains=word)
        
        decisions = Decision.objects.filter(q_filter).order_by('-decision_date')[:limit]
        
        for decision in decisions:
            documents.append(self._decision_to_document(decision))
        
        return documents
    
    def _decision_to_document(self, decision: Decision) -> Document:
        """Convert Decision to Document."""
        content_parts = []
        
        if decision.description:
            content_parts.append(f"Description: {decision.description}")
        if decision.rationale:
            content_parts.append(f"Rationale: {decision.rationale}")
        if decision.alternatives_considered:
            content_parts.append(f"Alternatives: {decision.alternatives_considered}")
        if decision.impact:
            content_parts.append(f"Impact: {decision.impact}")
        
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
            }
        )
    
    # =========================================
    # DOCUMENTATION QUERIES
    # =========================================
    
    def _retrieve_documentation(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve Confluence documentation."""
        documents = []
        
        q_filter = Q()
        
        for entity in entities:
            if isinstance(entity, str):
                q_filter |= Q(title__icontains=entity)
                q_filter |= Q(content__icontains=entity)
        
        keywords = ['setup', 'install', 'configure', 'guide', 'start', 'api', 'architecture']
        for keyword in keywords:
            if keyword in query.lower():
                q_filter |= Q(title__icontains=keyword)
                q_filter |= Q(content__icontains=keyword)
        
        pages = ConfluencePage.objects.filter(q_filter)[:limit]
        
        for page in pages:
            documents.append(self._confluence_to_document(page))
        
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
                'author': page.author,
                'labels': page.labels,
            }
        )
    
    # =========================================
    # TICKET QUERIES
    # =========================================
    
    def _retrieve_ticket_info(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve ticket information."""
        documents = []
        
        ticket_ids = [e for e in entities if isinstance(e, str) and 'ONBOARD-' in e.upper()]
        
        for ticket_id in ticket_ids:
            ticket = JiraTicket.objects.filter(issue_key__iexact=ticket_id).first()
            
            if ticket:
                documents.append(self._ticket_to_document(ticket))
                
                commits = GitCommit.objects.filter(message__icontains=ticket_id)[:3]
                for commit in commits:
                    documents.append(self._commit_to_document(commit))
                
                decisions = Decision.objects.filter(related_tickets__contains=[ticket_id])[:2]
                for decision in decisions:
                    documents.append(self._decision_to_document(decision))
        
        return documents[:limit]
    
    def _ticket_to_document(self, ticket: JiraTicket) -> Document:
        """Convert JiraTicket to Document."""
        content_parts = [
            f"Status: {ticket.status}",
            f"Assignee: {ticket.assignee or 'Unassigned'}",
        ]
        
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
            metadata={'status': ticket.status, 'priority': ticket.priority}
        )
    
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
            metadata={'sha': commit.sha}
        )
    
    # =========================================
    # MEETING & TIMELINE QUERIES
    # =========================================
    
    def _retrieve_meetings(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve meetings."""
        documents = []
        
        q_filter = Q()
        
        for entity in entities:
            if isinstance(entity, str):
                q_filter |= Q(title__icontains=entity)
                q_filter |= Q(summary__icontains=entity)
        
        for mtype in ['planning', 'standup', 'retrospective', 'review', 'midsprint']:
            if mtype in query.lower():
                q_filter |= Q(title__icontains=mtype)
        
        sprint_num = self._extract_sprint_number(query, entities)
        if sprint_num:
            q_filter |= Q(title__icontains=f'sprint{sprint_num}')
            q_filter |= Q(title__icontains=f'Sprint{sprint_num}')
        
        meetings = Meeting.objects.filter(q_filter).order_by('-meeting_date')[:limit]
        
        for meeting in meetings:
            documents.append(self._meeting_to_document(meeting))
        
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
        
        return Document(
            content="\n".join(content_parts),
            title=meeting.title or "Meeting",
            source_type='meeting',
            source_id=str(meeting.id),
            source_table='meetings',
            date=meeting.meeting_date.date() if meeting.meeting_date else None,
            related_people=[],
            metadata={}
        )
    
    def _retrieve_timeline(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """Retrieve timeline."""
        documents = []
        
        sprint_num = self._extract_sprint_number(query, entities)
        
        if sprint_num:
            try:
                sprint = Sprint.objects.get(sprint_number=sprint_num)
                decisions = Decision.objects.filter(
                    decision_date__gte=sprint.start_date,
                    decision_date__lte=sprint.end_date
                ).order_by('decision_date')
                
                for decision in decisions:
                    documents.append(self._decision_to_document(decision))
            except Sprint.DoesNotExist:
                pass
        
        if not documents:
            decisions = Decision.objects.filter(status='active').order_by('decision_date')[:limit]
            for decision in decisions:
                documents.append(self._decision_to_document(decision))
        
        return documents[:limit]
    
    def _retrieve_general(self, query: str, entities: List[str], limit: int) -> List[Document]:
        """General fallback."""
        documents = []
        
        decisions = Decision.objects.filter(status='active').order_by('-decision_date')[:3]
        for d in decisions:
            documents.append(self._decision_to_document(d))
        
        overview = ConfluencePage.objects.filter(
            Q(title__icontains='overview') | Q(title__icontains='project')
        ).first()
        if overview:
            documents.append(self._confluence_to_document(overview))
        
        return documents[:limit]


if __name__ == "__main__":
    print("Testing SQL Retriever v3...")
    retriever = SQLRetriever()
    
    tests = [
        ("person_query", ["Marcus"], "What has Marcus been working on?"),
        ("person_query", ["Lisa Park"], "Who worked on the frontend?"),
        ("general_query", [], "What Confluence pages are available?"),
    ]
    
    for intent, entities, query in tests:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        docs = retriever.retrieve(query, intent, entities, limit=5)
        print(f"Found {len(docs)} documents:")
        for d in docs:
            print(f"  - {d.source_type}: {d.title[:50]}")
