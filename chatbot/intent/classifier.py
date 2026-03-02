"""
Intent Classifier for Onboarding AI Chatbot
"""

import re
from typing import List, Tuple
from .types import IntentType, ClassifiedIntent, INTENT_CONFIGS


class IntentClassifier:
    PATTERNS = {
        'ticket_id': r'\b(ONBOARD-\d+)\b',
        'person_name': r'\b(Sarah Chen|Marcus Thompson|Lisa Park|Priya Sharma)\b',
        'sprint': r'\b[Ss]print\s*(\d+)\b',
    }
    
    def __init__(self, use_llm_fallback: bool = False, llm=None):
        self.use_llm_fallback = use_llm_fallback
        self.llm = llm
    
    def classify(self, query: str) -> ClassifiedIntent:
        query_lower = query.lower().strip()
        entities = self._extract_entities(query)
        
        # Direct ticket reference = ticket query
        if self._has_ticket_reference(query):
            return ClassifiedIntent(IntentType.TICKET_QUERY, 0.95, entities, query)
        
        # Score intents by keyword matches
        intent_scores = self._score_intents(query_lower)
        best_intent, best_score = self._get_best_intent(intent_scores)
        confidence = self._calculate_confidence(best_score, entities, query_lower)
        
        return ClassifiedIntent(best_intent, confidence, entities, query)
    
    def _extract_entities(self, query: str) -> List[str]:
        entities = []
        for pattern in self.PATTERNS.values():
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)
        
        # Extract tech terms
        tech_keywords = ['react', 'django', 'postgresql', 'jwt', 'authentication', 
                        'tailwind', 'material ui', 'aws', 'ecs', 'fargate']
        for term in tech_keywords:
            if term in query.lower():
                entities.append(term)
        
        return list(set(entities))
    
    def _has_ticket_reference(self, query: str) -> bool:
        return bool(re.search(self.PATTERNS['ticket_id'], query, re.IGNORECASE))
    
    def _score_intents(self, query_lower: str) -> dict:
        scores = {}
        for intent_type, config in INTENT_CONFIGS.items():
            score = sum(1 for kw in config.keywords if kw in query_lower)
            scores[intent_type] = score
        return scores
    
    def _get_best_intent(self, scores: dict) -> Tuple[IntentType, float]:
        if all(s == 0 for s in scores.values()):
            return IntentType.GENERAL_QUERY, 0.0
        return max(scores.items(), key=lambda x: x[1])
    
    def _calculate_confidence(self, score: float, entities: List[str], query: str) -> float:
        if score == 0:
            return 0.3
        confidence = min(0.5 + (score * 0.15), 0.9)
        if entities:
            confidence += 0.1
        return min(confidence, 0.95)
    
    def classify_with_explanation(self, query: str) -> Tuple[ClassifiedIntent, str]:
        result = self.classify(query)
        explanation = f"Query: {query}\nIntent: {result.intent_type.value}\nConfidence: {result.confidence:.2f}\nEntities: {result.entities}"
        return result, explanation


def classify_query(query: str) -> ClassifiedIntent:
    return IntentClassifier().classify(query)


if __name__ == "__main__":
    test_queries = [
        "Why did we choose React?",
        "Who worked on authentication?",
        "What happened in Sprint 1?",
        "How do I set up the project?",
        "What's the status of ONBOARD-15?",
        "Tell me about ONBOARD-14",
        "who will the project work"
    ]
    
    classifier = IntentClassifier()
    for q in test_queries:
        result, exp = classifier.classify_with_explanation(q)
        print(f"\n{exp}\n" + "-"*40)