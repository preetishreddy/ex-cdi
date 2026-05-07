"""
Base Retriever Interface

This abstract class defines the interface that all retrievers must implement.
This allows easy swapping between:
- Phase 1: SQLRetriever (direct SQL queries)
- Phase 2: HybridRetriever (SQL + PGVector)
- Phase 3: RAGRetriever (full vector search)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date


@dataclass
class Document:
    """
    Represents a retrieved document/record.
    
    This is a universal format that works across all retriever types.
    Whether data comes from SQL, vector search, or RAG - it's converted to this format.
    """
    
    # Content
    content: str                          # Main text content
    title: str = ""                       # Title/summary
    
    # Metadata
    source_type: str = ""                 # 'decision', 'meeting', 'jira', 'confluence', 'commit'
    source_id: str = ""                   # UUID of source record
    source_table: str = ""                # Database table name
    
    # Temporal
    date: Optional[date] = None           # Relevant date
    
    # Relationships
    related_tickets: List[str] = field(default_factory=list)
    related_people: List[str] = field(default_factory=list)
    
    # Relevance
    relevance_score: float = 1.0          # How relevant to the query (0-1)
    
    # Extra metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self):
        return f"Document({self.source_type}: {self.title[:50]})"
    
    def to_context_string(self) -> str:
        """Convert to string for LLM context."""
        parts = []
        
        if self.title:
            parts.append(f"TITLE: {self.title}")
        
        if self.source_type:
            parts.append(f"SOURCE: {self.source_type}")
        
        if self.date:
            parts.append(f"DATE: {self.date}")
        
        if self.related_people:
            parts.append(f"PEOPLE: {', '.join(self.related_people)}")
        
        if self.related_tickets:
            parts.append(f"TICKETS: {', '.join(self.related_tickets)}")
        
        parts.append(f"CONTENT:\n{self.content}")
        
        return "\n".join(parts)


class BaseRetriever(ABC):
    """
    Abstract base class for all retrievers.
    
    Implement this interface to create new retriever types:
    - SQLRetriever: Direct database queries (Phase 1)
    - HybridRetriever: SQL + Vector search (Phase 2)
    - RAGRetriever: Full RAG pipeline (Phase 3)
    """
    
    @abstractmethod
    def retrieve(
        self, 
        query: str, 
        intent_type: str, 
        entities: List[str],
        limit: int = 10
    ) -> List[Document]:
        """
        Retrieve relevant documents based on query and intent.
        
        Args:
            query: The user's original query
            intent_type: Classified intent (e.g., 'decision_query')
            entities: Extracted entities (ticket IDs, names, terms)
            limit: Maximum number of documents to return
            
        Returns:
            List of Document objects, sorted by relevance
        """
        pass
    
    @abstractmethod
    def retrieve_by_id(self, source_type: str, source_id: str) -> Optional[Document]:
        """
        Retrieve a specific document by its ID.
        
        Args:
            source_type: Type of source ('decision', 'meeting', etc.)
            source_id: UUID of the record
            
        Returns:
            Document if found, None otherwise
        """
        pass
    
    def health_check(self) -> bool:
        """Check if the retriever is working properly."""
        return True