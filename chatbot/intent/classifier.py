"""
Intent Classifier for Onboarding AI Chatbot (v3)

Fixes:
1. Better person name detection
2. List query support
3. Role/topic to person mapping
"""

import re
from typing import List, Tuple, Optional

from .types import (
    IntentType, 
    ClassifiedIntent, 
    INTENT_CONFIGS,
    ENTITY_PATTERNS,
    TECH_TERMS
)


class IntentClassifier:
    """Rule-based intent classifier with improved person detection."""
    
    # Known person names (first names and full names)
    PERSON_NAMES = [
        'sarah', 'sarah chen',
        'marcus', 'marcus thompson',
        'lisa', 'lisa park',
        'priya', 'priya sharma',
        'james', "james o'brien",
        'dave', 'dave rossi',
    ]
    
    # Role keywords that map to person queries
    ROLE_KEYWORDS = [
        'frontend', 'front-end', 'ui', 'react',
        'backend', 'back-end', 'api', 'authentication', 'auth',
        'database', 'db', 'schema',
        'devops', 'ci/cd', 'deployment', 'pipeline',
    ]
    
    def __init__(self):
        self.intent_configs = INTENT_CONFIGS
        self.entity_patterns = ENTITY_PATTERNS
        self.tech_terms = TECH_TERMS
    
    def classify(self, query: str) -> ClassifiedIntent:
        """Classify a user query into an intent type."""
        query_lower = query.lower()
        
        # Step 1: Extract entities
        entities = self._extract_entities(query)
        
        # Step 2: Check for list query
        if self._is_list_query(query_lower):
            return ClassifiedIntent(
                intent_type=IntentType.GENERAL_QUERY,  # Will be handled by retriever
                confidence=0.85,
                entities=entities,
                original_query=query
            )
        
        # Step 3: Check for sprint summary query
        if self._is_sprint_summary_query(query_lower, entities):
            return ClassifiedIntent(
                intent_type=IntentType.SPRINT_SUMMARY_QUERY,
                confidence=0.90,
                entities=entities,
                original_query=query
            )
        
        # Step 4: Check for person query (IMPROVED)
        if self._is_person_query(query_lower, entities):
            return ClassifiedIntent(
                intent_type=IntentType.PERSON_QUERY,
                confidence=0.90,
                entities=entities,
                original_query=query
            )
        
        # Step 5: Check for direct ticket reference
        ticket_ids = [e for e in entities if 'ONBOARD-' in e.upper()]
        if ticket_ids and not self._has_decision_keywords(query_lower):
            return ClassifiedIntent(
                intent_type=IntentType.TICKET_QUERY,
                confidence=0.95,
                entities=entities,
                original_query=query
            )
        
        # Step 6: Score all intents
        scores = self._score_intents(query_lower)
        
        # Step 7: Get best intent
        best_intent, score = self._get_best_intent(scores)
        
        # Step 8: Calculate confidence
        confidence = self._calculate_confidence(score, entities, query_lower)
        
        return ClassifiedIntent(
            intent_type=best_intent,
            confidence=confidence,
            entities=entities,
            original_query=query
        )
    
    def _is_list_query(self, query_lower: str) -> bool:
        """Check if query is asking for a list."""
        list_patterns = [
            'list all', 'show all', 'what are all',
            'all the', 'available', 'what pages',
            'what documents', 'what decisions',
            'what meetings', 'what tickets',
            'how many'
        ]
        return any(pattern in query_lower for pattern in list_patterns)
    
    def _is_person_query(self, query_lower: str, entities: List[str]) -> bool:
        """
        Check if query is asking about a person.
        
        Improved to detect:
        1. Direct person names
        2. Role keywords (frontend, backend, etc.)
        3. "who" questions about roles
        """
        # Check for person names in entities
        has_person = any(
            name.lower() in query_lower or name.lower() in [e.lower() for e in entities]
            for name in self.PERSON_NAMES
        )
        
        if has_person:
            return True
        
        # Check for "who" + role pattern
        who_patterns = [
            r'who\s+(worked|works|is working|did|does|made|created|wrote|authored)',
            r'who\s+is\s+(responsible|assigned|the\s+author)',
            r'contact.*for\s+(frontend|backend|api|database)',
            r'(frontend|backend|api|database).*contact',
        ]
        
        for pattern in who_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check for role keywords with person-related questions
        person_question_words = ['who', 'contact', 'reach', 'ask', 'talk to', 'worked on', 'responsible']
        has_role_keyword = any(role in query_lower for role in self.ROLE_KEYWORDS)
        has_person_question = any(word in query_lower for word in person_question_words)
        
        if has_role_keyword and has_person_question:
            return True
        
        # Check for possessive patterns with names
        possessive_patterns = [
            r"(marcus|sarah|lisa|priya|james|dave)('s|s')",
            r"(his|her)\s+(commits|tickets|work|contributions)",
        ]
        
        for pattern in possessive_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def _is_sprint_summary_query(self, query_lower: str, entities: List[str]) -> bool:
        """Check if query is asking for a sprint summary."""
        has_sprint_number = any(e.isdigit() for e in entities if isinstance(e, str))
        
        summary_keywords = [
            'summary', 'summarize', 'overview', 'recap', 'highlights',
            'accomplishments', 'report', 'insights', 'analysis',
            'what happened in sprint', 'tell me about sprint'
        ]
        
        has_sprint_word = 'sprint' in query_lower
        has_summary_keyword = any(kw in query_lower for kw in summary_keywords)
        
        sprint_summary_pattern = bool(re.search(
            r'(summary|overview|recap|summarize).{0,20}sprint\s*\d+|sprint\s*\d+.{0,20}(summary|overview|recap)',
            query_lower
        ))
        
        what_happened_pattern = bool(re.search(
            r'what.{0,10}(happened|occurred|done|achieved).{0,10}sprint\s*\d+',
            query_lower
        ))
        
        return (
            sprint_summary_pattern or
            what_happened_pattern or
            (has_sprint_word and has_summary_keyword and has_sprint_number)
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from the query."""
        entities = []
        query_lower = query.lower()
        
        # Extract ticket IDs
        ticket_matches = re.findall(
            self.entity_patterns['ticket_id'], 
            query, 
            re.IGNORECASE
        )
        entities.extend([t.upper() for t in ticket_matches])
        
        # Extract sprint numbers
        sprint_matches = re.findall(
            self.entity_patterns['sprint_number'],
            query,
            re.IGNORECASE
        )
        entities.extend(sprint_matches)
        
        # Extract person names (IMPROVED - check for partial matches)
        for name in self.PERSON_NAMES:
            if name in query_lower:
                # Prefer full name if available
                if ' ' in name:
                    entities.append(name.title())
                elif name + ' ' not in query_lower:  # Don't add first name if full name is there
                    entities.append(name.title())
        
        # Extract tech terms
        for term in self.tech_terms:
            if term in query_lower:
                entities.append(term)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for e in entities:
            e_lower = e.lower()
            if e_lower not in seen:
                seen.add(e_lower)
                unique_entities.append(e)
        
        return unique_entities
    
    def _has_decision_keywords(self, query_lower: str) -> bool:
        """Check if query has decision-related keywords."""
        decision_keywords = ['why', 'decision', 'chose', 'rationale', 'reason']
        return any(kw in query_lower for kw in decision_keywords)
    
    def _score_intents(self, query_lower: str) -> dict:
        """Score each intent type based on keyword matches."""
        scores = {}
        
        for intent_type, config in self.intent_configs.items():
            if intent_type == IntentType.SPRINT_SUMMARY_QUERY:
                continue
                
            score = 0
            matched_keywords = []
            
            for keyword in config.keywords:
                if keyword in query_lower:
                    weight = len(keyword.split())
                    
                    # Boost for specific keywords
                    if keyword in ['meeting', 'discussed', 'standup', 'planning']:
                        weight *= 1.5
                    
                    score += weight
                    matched_keywords.append(keyword)
            
            if len(matched_keywords) > 1:
                score *= 1.2
            
            scores[intent_type] = score
        
        return scores
    
    def _get_best_intent(self, scores: dict) -> Tuple[IntentType, float]:
        """Get the intent with highest score."""
        if not scores or all(s == 0 for s in scores.values()):
            return IntentType.GENERAL_QUERY, 0.0
        
        best_intent = max(scores, key=scores.get)
        return best_intent, scores[best_intent]
    
    def _calculate_confidence(
        self, 
        score: float, 
        entities: List[str], 
        query_lower: str
    ) -> float:
        """Calculate confidence score."""
        if score == 0:
            return 0.3
        
        confidence = min(0.5 + (score * 0.1), 0.95)
        
        if entities:
            confidence += 0.1
        
        question_words = ['what', 'why', 'how', 'who', 'when', 'where']
        if any(qw in query_lower for qw in question_words):
            confidence += 0.05
        
        return min(confidence, 0.95)
    
    def classify_with_explanation(self, query: str) -> Tuple[ClassifiedIntent, str]:
        """Classify with detailed explanation."""
        result = self.classify(query)
        
        query_lower = query.lower()
        scores = self._score_intents(query_lower)
        
        lines = [
            f"Query: {query}",
            f"Entities: {result.entities}",
            "",
            "Scores:",
        ]
        
        for intent, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            marker = "→" if intent == result.intent_type else " "
            lines.append(f"  {marker} {intent.value}: {score:.2f}")
        
        lines.extend([
            "",
            f"Selected: {result.intent_type.value}",
            f"Confidence: {result.confidence:.2f}",
        ])
        
        return result, "\n".join(lines)


def test_classifier():
    """Test the classifier."""
    classifier = IntentClassifier()
    
    test_queries = [
        # Person queries (should all be person_query)
        "What has Marcus been working on?",
        "Who worked on the frontend?",
        "Show me Lisa's commits",
        "Who should I contact for backend questions?",
        "What are Marcus's contributions?",
        
        # Decision queries
        "Why did we choose React?",
        "What was the rationale for PostgreSQL?",
        
        # Sprint queries
        "What's the summary of Sprint 1?",
        "Sprint 2 status",
        
        # List queries
        "What Confluence pages are available?",
        "List all decisions",
        
        # Ticket queries
        "Tell me about ONBOARD-14",
    ]
    
    print("=" * 60)
    print("INTENT CLASSIFIER TEST v3")
    print("=" * 60)
    
    for query in test_queries:
        result = classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"  Intent: {result.intent_type.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Entities: {result.entities}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_classifier()
