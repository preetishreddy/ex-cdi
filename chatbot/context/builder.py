"""
Context Builder for Onboarding AI Chatbot (Conversational Version)

Transforms retrieved documents into structured context for LLM.
Supports conversation history integration.
"""

from typing import List, Optional
try:
    from .retriever.base import Document
except ImportError:
    from retriever.base import Document

try:
    from .templates import PromptTemplates
except ImportError:
    from templates import PromptTemplates


class ContextBuilder:
    """
    Builds structured context from retrieved documents.
    
    Features:
    - Formats documents based on their type
    - Handles superseded decisions
    - Limits context size for LLM token limits
    - Prioritizes most relevant information
    - Supports conversation history integration
    """
    
    MAX_CONTEXT_CHARS = 8000  # Approximate limit to stay within token limits
    MAX_HISTORY_CHARS = 1500  # Limit for conversation history
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_context(self, documents: List[Document], intent_type: str) -> str:
        """
        Build context string from documents.
        
        Args:
            documents: List of retrieved documents
            intent_type: The classified intent type
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant information found in the knowledge base."
        
        # Sort by relevance score
        sorted_docs = sorted(documents, key=lambda d: d.relevance_score, reverse=True)
        
        # Build context sections
        sections = []
        total_chars = 0
        
        for doc in sorted_docs:
            section = self._format_document(doc)
            
            # Check if we have room
            if total_chars + len(section) > self.MAX_CONTEXT_CHARS:
                # Add truncated version if this is first doc
                if not sections:
                    sections.append(section[:self.MAX_CONTEXT_CHARS])
                break
            
            sections.append(section)
            total_chars += len(section)
        
        return "\n\n---\n\n".join(sections)
    
    def build_context_with_history(
        self, 
        documents: List[Document], 
        intent_type: str,
        conversation_history: str = None
    ) -> str:
        """
        Build context string including conversation history.
        
        Args:
            documents: List of retrieved documents
            intent_type: The classified intent type
            conversation_history: Summary of previous conversation turns
            
        Returns:
            Formatted context string with history
        """
        # Build document context
        doc_context = self.build_context(documents, intent_type)
        
        if not conversation_history:
            return doc_context
        
        # Truncate history if needed
        if len(conversation_history) > self.MAX_HISTORY_CHARS:
            conversation_history = conversation_history[:self.MAX_HISTORY_CHARS] + "\n[Earlier conversation truncated...]"
        
        # Combine history and document context
        return f"""CONVERSATION HISTORY:
{conversation_history}

---

RELEVANT INFORMATION FROM DATABASE:
{doc_context}"""
    
    def build_prompt(self, documents: List[Document], intent_type: str, query: str) -> str:
        """
        Build complete prompt with context and query.
        
        Args:
            documents: List of retrieved documents
            intent_type: The classified intent type
            query: The user's original query
            
        Returns:
            Complete prompt ready for LLM
        """
        context = self.build_context(documents, intent_type)
        template_fn = self.templates.get_template(intent_type)
        return template_fn(context, query)
    
    def build_conversational_prompt(
        self,
        documents: List[Document],
        intent_type: str,
        query: str,
        conversation_history: str = None
    ) -> str:
        """
        Build prompt with conversation history for multi-turn conversations.
        
        Args:
            documents: List of retrieved documents
            intent_type: The classified intent type
            query: The user's current query
            conversation_history: Summary of previous turns
            
        Returns:
            Complete prompt with history context
        """
        context = self.build_context_with_history(documents, intent_type, conversation_history)
        
        intent_instructions = {
            'decision_query': "Focus on explaining the decision, its rationale, and alternatives considered.",
            'person_query': "Focus on the person's contributions and involvement in the project.",
            'timeline_query': "Focus on chronological order and key milestones.",
            'howto_query': "Focus on providing clear, step-by-step instructions.",
            'status_query': "Focus on current status, assignee, and any blockers.",
            'ticket_query': "Focus on ticket details, related work, and current state.",
            'meeting_query': "Focus on what was discussed, decisions made, and action items.",
            'general_query': "Provide helpful information based on the context.",
        }
        
        instruction = intent_instructions.get(intent_type, intent_instructions['general_query'])
        
        prompt = f"""You are an AI assistant for the Employee Onboarding Portal project.
You are having a CONVERSATION with a team member. Use any conversation history to understand context and references.

INSTRUCTIONS: {instruction}

IMPORTANT RULES:
1. Only answer based on the provided context
2. If the user refers to "it", "that", "they", etc., use the conversation history to understand what they mean
3. If information is marked as "superseded", mention that newer decisions exist
4. Always cite your sources (meeting name, ticket ID, etc.)
5. If you don't have enough information, say so clearly
6. Be concise but complete
7. Maintain continuity with previous responses

CONTEXT:
{context}

CURRENT QUESTION: {query}

Provide a helpful, accurate answer:"""
        
        return prompt
    
    def _format_document(self, doc: Document) -> str:
        """Format a single document based on its type."""
        formatters = {
            'decision': self._format_decision,
            'meeting': self._format_meeting,
            'jira': self._format_ticket,
            'confluence': self._format_confluence,
            'commit': self._format_commit,
        }
        
        formatter = formatters.get(doc.source_type, self._format_generic)
        return formatter(doc)
    
    def _format_decision(self, doc: Document) -> str:
        """Format a decision document."""
        lines = [
            f"📋 DECISION: {doc.title}",
            f"Date: {doc.date}" if doc.date else None,
            f"Category: {doc.metadata.get('category', 'N/A')}",
            f"Status: {doc.metadata.get('status', 'active')}",
        ]
        
        if doc.related_people:
            lines.append(f"Decided by: {', '.join(doc.related_people)}")
        
        if doc.related_tickets:
            lines.append(f"Related tickets: {', '.join(doc.related_tickets)}")
        
        lines.append("")  # Empty line before content
        lines.append(doc.content)
        
        # Mark if superseded
        if doc.metadata.get('is_superseded'):
            lines.insert(1, "⚠️ NOTE: This decision has been SUPERSEDED by a newer decision")
        
        return "\n".join(line for line in lines if line is not None)
    
    def _format_meeting(self, doc: Document) -> str:
        """Format a meeting document."""
        lines = [
            f"🗓️ MEETING: {doc.title}",
            f"Date: {doc.date}" if doc.date else None,
        ]
        
        if doc.related_people:
            lines.append(f"Participants: {', '.join(doc.related_people)}")
        
        lines.append("")
        lines.append(doc.content)
        
        return "\n".join(line for line in lines if line is not None)
    
    def _format_ticket(self, doc: Document) -> str:
        """Format a Jira ticket document."""
        lines = [
            f"🎫 TICKET: {doc.title}",
            f"Status: {doc.metadata.get('status', 'Unknown')}",
            f"Type: {doc.metadata.get('issue_type', 'Unknown')}",
        ]
        
        if doc.metadata.get('priority'):
            lines.append(f"Priority: {doc.metadata['priority']}")
        
        if doc.related_people:
            lines.append(f"Assignee: {doc.related_people[0] if doc.related_people else 'Unassigned'}")
        
        if doc.metadata.get('sprint'):
            lines.append(f"Sprint: {doc.metadata['sprint']}")
        
        lines.append("")
        lines.append(doc.content)
        
        return "\n".join(line for line in lines if line is not None)
    
    def _format_confluence(self, doc: Document) -> str:
        """Format a Confluence page document."""
        lines = [
            f"📄 DOCUMENTATION: {doc.title}",
            f"Author: {doc.related_people[0] if doc.related_people else 'Unknown'}",
        ]
        
        if doc.date:
            lines.append(f"Created: {doc.date}")
        
        lines.append("")
        
        # Truncate long content
        content = doc.content
        if len(content) > 2000:
            content = content[:2000] + "\n\n[Content truncated...]"
        
        lines.append(content)
        
        return "\n".join(lines)
    
    def _format_commit(self, doc: Document) -> str:
        """Format a git commit document."""
        lines = [
            f"💻 COMMIT: {doc.title}",
            f"Author: {doc.related_people[0] if doc.related_people else 'Unknown'}",
            f"Date: {doc.date}" if doc.date else None,
        ]
        
        if doc.metadata.get('sha'):
            lines.append(f"SHA: {doc.metadata['sha'][:8]}")
        
        if doc.related_tickets:
            lines.append(f"Related tickets: {', '.join(doc.related_tickets)}")
        
        return "\n".join(line for line in lines if line is not None)
    
    def _format_generic(self, doc: Document) -> str:
        """Format a generic document."""
        lines = [
            f"📌 {doc.source_type.upper()}: {doc.title}",
            f"Date: {doc.date}" if doc.date else None,
            "",
            doc.content,
        ]
        return "\n".join(line for line in lines if line is not None)


# =========================================
# TEST FUNCTION
# =========================================

def test_context_builder():
    """Test the context builder with conversation history."""
    try:
        from .retriever.base import Document
    except ImportError:
        from retriever.base import Document
    from datetime import date
    
    # Create sample documents
    docs = [
        Document(
            content="Rationale: React has strong community support and team expertise.\nAlternatives: Vue, Angular",
            title="Use React for frontend",
            source_type="decision",
            source_id="123",
            source_table="decisions",
            date=date(2026, 1, 6),
            related_people=["Sarah Chen", "Marcus Thompson"],
            related_tickets=["ONBOARD-13"],
            metadata={'category': 'technology', 'status': 'active'}
        ),
    ]
    
    # Sample conversation history
    history = """User: What tech stack are we using?
Assistant: The project uses Django for backend, React for frontend, and PostgreSQL for the database.

User: Tell me more about the frontend choice."""
    
    builder = ContextBuilder()
    
    print("=" * 60)
    print("CONTEXT BUILDER TEST (with Conversation History)")
    print("=" * 60)
    
    # Test with history
    context = builder.build_context_with_history(docs, "decision_query", history)
    print("\n📋 Context with History:")
    print("-" * 40)
    print(context[:1000] + "..." if len(context) > 1000 else context)
    
    # Test conversational prompt
    prompt = builder.build_conversational_prompt(
        docs, 
        "decision_query", 
        "Who made that decision?",
        history
    )
    print("\n📝 Conversational Prompt:")
    print("-" * 40)
    print(prompt[:1500] + "..." if len(prompt) > 1500 else prompt)
    
    print("\n" + "=" * 60)
    print("TEST PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_context_builder()
