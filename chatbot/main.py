"""
Onboarding AI Chatbot - Main Entry Point (Conversational Version)

This is the main chatbot class that orchestrates:
1. Conversation History - Remember previous messages
2. Intent Classification - Understand what user is asking
3. Retrieval - Fetch relevant data from PostgreSQL
4. Context Building - Format data for LLM with history
5. Response Generation - Generate helpful response

Usage:
    # From chatbot directory:
    python main.py
    
    # From parent directory:
    python -c "from chatbot import OnboardingChatbot; bot = OnboardingChatbot()"
"""

from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass, field
from datetime import datetime

# Handle both package import and direct execution
try:
    # When imported as package (from chatbot import OnboardingChatbot)
    from .intent import IntentClassifier, ClassifiedIntent, IntentType
    from .retriever import SQLRetriever, Document
    from .context import ContextBuilder
    from .llm import BytezLLM
except ImportError:
    # When run directly (python -m main or python main.py)
    from intent import IntentClassifier, ClassifiedIntent, IntentType
    from retriever import SQLRetriever, Document
    from context import ContextBuilder
    from llm import BytezLLM


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: str = None
    entities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'intent': self.intent,
            'entities': self.entities
        }


class ConversationHistory:
    """
    Manages conversation history for multi-turn conversations.
    
    Features:
    - Stores messages with metadata
    - Extracts context from recent turns
    - Resolves references ("it", "that", "they")
    - Limits history to avoid token overflow
    """
    
    MAX_HISTORY_TURNS = 10  # Keep last N exchanges
    
    def __init__(self):
        self.messages: List[Message] = []
        self.current_topic: str = None
        self.current_entities: List[str] = []
    
    def add_user_message(self, content: str, intent: str = None, entities: List[str] = None):
        """Add a user message to history."""
        message = Message(
            role='user',
            content=content,
            intent=intent,
            entities=entities or []
        )
        self.messages.append(message)
        
        # Update current context
        if entities:
            self.current_entities = entities
        if intent:
            self.current_topic = intent
        
        self._trim_history()
    
    def add_assistant_message(self, content: str):
        """Add an assistant response to history."""
        message = Message(
            role='assistant',
            content=content
        )
        self.messages.append(message)
        self._trim_history()
    
    def _trim_history(self):
        """Keep only recent messages to manage token limits."""
        max_messages = self.MAX_HISTORY_TURNS * 2  # User + Assistant pairs
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
    
    def get_context_summary(self) -> str:
        """Get a summary of recent conversation for context."""
        if not self.messages:
            return ""
        
        summary_parts = []
        
        # Get last few exchanges
        recent = self.messages[-6:]  # Last 3 exchanges
        
        for msg in recent:
            role = "User" if msg.role == 'user' else "Assistant"
            # Truncate long messages
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            summary_parts.append(f"{role}: {content}")
        
        return "\n".join(summary_parts)
    
    def get_recent_entities(self) -> List[str]:
        """Get entities mentioned in recent conversation."""
        entities = set()
        
        for msg in self.messages[-6:]:
            entities.update(msg.entities)
        
        # Add current entities
        entities.update(self.current_entities)
        
        return list(entities)
    
    def get_last_user_query(self) -> Optional[str]:
        """Get the last user query."""
        for msg in reversed(self.messages):
            if msg.role == 'user':
                return msg.content
        return None
    
    def resolve_references(self, query: str) -> str:
        """
        Resolve pronouns and references using conversation context.
        
        Examples:
        - "Tell me more about it" → "Tell me more about React"
        - "Who else worked on that?" → "Who else worked on authentication?"
        """
        # Reference words to check
        reference_words = ['it', 'that', 'this', 'they', 'them', 'those', 'the decision', 'the ticket']
        
        query_lower = query.lower()
        
        # Check if query contains reference words
        has_reference = any(ref in query_lower for ref in reference_words)
        
        if has_reference and self.current_entities:
            # Get the most recent/relevant entity
            main_entity = self.current_entities[0] if self.current_entities else None
            
            if main_entity:
                # Add context hint to query
                return f"{query} (referring to: {main_entity})"
        
        return query
    
    def clear(self):
        """Clear conversation history."""
        self.messages = []
        self.current_topic = None
        self.current_entities = []
    
    def __len__(self):
        return len(self.messages)


@dataclass
class ChatResponse:
    """Structured response from the chatbot."""
    answer: str
    intent: str
    confidence: float
    sources: List[str]
    entities: List[str]
    conversation_turn: int = 0
    
    def __str__(self):
        return self.answer


class OnboardingChatbot:
    """
    Main chatbot class for the Onboarding AI project (Conversational Version).
    
    Orchestrates the full pipeline with conversation memory:
    Query + History → Intent Classification → Retrieval → Context Building → LLM → Response
    
    Example:
        bot = OnboardingChatbot()
        
        # First turn
        response = bot.chat("Why did we choose React?")
        print(response)
        
        # Follow-up (bot remembers context)
        response = bot.chat("Who made that decision?")
        print(response)  # Knows "that decision" = React decision
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the chatbot.
        
        Args:
            verbose: If True, print debug information
        """
        self.verbose = verbose
        
        # Initialize components
        self._log("Initializing chatbot components...")
        
        self.classifier = IntentClassifier()
        self._log("  ✓ Intent Classifier loaded")
        
        self.retriever = SQLRetriever()
        self._log("  ✓ SQL Retriever loaded")
        
        self.context_builder = ContextBuilder()
        self._log("  ✓ Context Builder loaded")
        
        self.llm = BytezLLM()
        self._log("  ✓ LLM (Bytez/GPT-4o) loaded")
        
        # Initialize conversation history
        self.history = ConversationHistory()
        self._log("  ✓ Conversation History initialized")
        
        self._log("Chatbot ready! (Conversational Mode)")
    
    def _log(self, message: str):
        """Print debug message if verbose mode is on."""
        if self.verbose:
            print(message)
    
    def chat(self, query: str) -> ChatResponse:
        """
        Process a user query and return a response.
        Maintains conversation history for multi-turn conversations.
        
        Args:
            query: The user's question
            
        Returns:
            ChatResponse with answer and metadata
        """
        self._log(f"\n{'='*50}")
        self._log(f"Query: {query}")
        self._log(f"Conversation Turn: {len(self.history) // 2 + 1}")
        self._log('='*50)
        
        # Step 0: Resolve references from conversation history
        resolved_query = self.history.resolve_references(query)
        if resolved_query != query:
            self._log(f"\n0. Resolved references:")
            self._log(f"   Original: {query}")
            self._log(f"   Resolved: {resolved_query}")
        
        # Step 1: Classify intent
        self._log("\n1. Classifying intent...")
        intent = self.classifier.classify(resolved_query)
        
        # Enhance entities with conversation context
        all_entities = list(set(intent.entities + self.history.get_recent_entities()))
        
        self._log(f"   Intent: {intent.intent_type.value}")
        self._log(f"   Confidence: {intent.confidence:.2f}")
        self._log(f"   Entities: {all_entities}")
        
        # Step 2: Retrieve relevant documents
        self._log("\n2. Retrieving documents...")
        documents = self.retriever.retrieve(
            query=resolved_query,
            intent_type=intent.intent_type.value,
            entities=all_entities,
            limit=5
        )
        self._log(f"   Found {len(documents)} documents")
        for doc in documents:
            self._log(f"   • {doc.source_type}: {doc.title[:40]}")
        
        # Step 3: Build context with conversation history
        self._log("\n3. Building context...")
        context = self.context_builder.build_context(documents, intent.intent_type.value)
        
        # Add conversation history to context
        history_summary = self.history.get_context_summary()
        if history_summary:
            context = f"PREVIOUS CONVERSATION:\n{history_summary}\n\n---\n\nRELEVANT INFORMATION:\n{context}"
        
        self._log(f"   Context length: {len(context)} chars")
        self._log(f"   Includes history: {'Yes' if history_summary else 'No'}")
        
        # Step 4: Generate response
        self._log("\n4. Generating response...")
        prompt = self._build_conversational_prompt(context, query, intent.intent_type.value)
        answer = self.llm.generate(prompt)
        self._log(f"   Response length: {len(answer)} chars")
        
        # Step 5: Update conversation history
        self.history.add_user_message(
            content=query,
            intent=intent.intent_type.value,
            entities=intent.entities
        )
        self.history.add_assistant_message(content=answer)
        
        # Build response object
        sources = list(set(
            f"{doc.source_type}:{doc.title[:30]}" 
            for doc in documents
        ))
        
        return ChatResponse(
            answer=answer,
            intent=intent.intent_type.value,
            confidence=intent.confidence,
            sources=sources,
            entities=all_entities,
            conversation_turn=len(self.history) // 2
        )
    
    def _build_conversational_prompt(self, context: str, query: str, intent_type: str) -> str:
        """Build a prompt that includes conversation awareness."""
        
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
You are having a CONVERSATION with a team member. Use the conversation history to understand context and references.

INSTRUCTIONS: {instruction}

IMPORTANT RULES:
1. Only answer based on the provided context
2. If the user refers to "it", "that", "they", etc., use the conversation history to understand what they mean
3. If information is marked as "superseded", mention that newer decisions exist
4. Always cite your sources (meeting name, ticket ID, etc.)
5. If you don't have enough information, say so clearly
6. Be concise but complete
7. Maintain continuity with previous responses in the conversation

CONTEXT:
{context}

CURRENT QUESTION: {query}

Provide a helpful, accurate answer that takes into account the conversation history:"""
        
        return prompt
    
    def chat_simple(self, query: str) -> str:
        """
        Simple chat interface - returns just the answer string.
        
        Args:
            query: The user's question
            
        Returns:
            Answer string
        """
        response = self.chat(query)
        return response.answer
    
    def get_intent(self, query: str) -> Tuple[str, float, List[str]]:
        """
        Get just the intent classification for a query.
        
        Returns:
            Tuple of (intent_type, confidence, entities)
        """
        intent = self.classifier.classify(query)
        return (intent.intent_type.value, intent.confidence, intent.entities)
    
    def clear_history(self):
        """Clear conversation history to start fresh."""
        self.history.clear()
        self._log("Conversation history cleared.")
    
    def get_conversation_length(self) -> int:
        """Get the number of turns in current conversation."""
        return len(self.history) // 2
    
    def health_check(self) -> dict:
        """
        Check if all components are working.
        
        Returns:
            Dict with status of each component
        """
        status = {
            'classifier': 'ok',
            'retriever': 'ok',
            'context_builder': 'ok',
            'llm': self.llm.health_check(),
            'conversation_history': f'{len(self.history)} messages'
        }
        
        # Test retriever
        try:
            docs = self.retriever.retrieve("test", "general_query", [], limit=1)
            status['retriever'] = 'ok'
        except Exception as e:
            status['retriever'] = f'error: {str(e)}'
        
        return status


# =========================================
# INTERACTIVE CLI
# =========================================

def run_interactive():
    """Run an interactive chat session."""
    print("=" * 60)
    print("🤖 ONBOARDING AI CHATBOT (Conversational)")
    print("=" * 60)
    print("\nWelcome! I'm here to help you understand the Employee")
    print("Onboarding Portal project. I remember our conversation,")
    print("so feel free to ask follow-up questions!")
    print("\nAsk me about:")
    print("  • Project decisions and their rationale")
    print("  • Who worked on what")
    print("  • How to set up the project")
    print("  • Ticket status and details")
    print("  • Meeting discussions")
    print("\nCommands:")
    print("  'quit'  - Exit the chatbot")
    print("  'help'  - Show example questions")
    print("  'clear' - Clear conversation history")
    print("  'debug' - Toggle debug mode")
    print("")
    
    bot = OnboardingChatbot(verbose=False)
    
    # Check health
    health = bot.health_check()
    if health['llm']['status'] != 'ok':
        print(f"⚠️  Warning: LLM might not be working: {health['llm']['message']}")
    
    while True:
        try:
            # Show conversation turn
            turn = bot.get_conversation_length() + 1
            query = input(f"\n👤 You (turn {turn}): ").strip()
            
            if not query:
                continue
            
            if query.lower() == 'quit':
                print("\n👋 Goodbye!")
                break
            
            if query.lower() == 'help':
                print_help()
                continue
            
            if query.lower() == 'clear':
                bot.clear_history()
                print("🗑️  Conversation history cleared. Starting fresh!")
                continue
            
            if query.lower() == 'debug':
                bot.verbose = not bot.verbose
                print(f"🔧 Debug mode: {'ON' if bot.verbose else 'OFF'}")
                continue
            
            # Get response
            print("\n🤖 Assistant: ", end="")
            response = bot.chat(query)
            print(response.answer)
            
            # Show metadata
            print(f"\n   📊 Intent: {response.intent} | Confidence: {response.confidence:.0%}")
            if response.sources:
                print(f"   📚 Sources: {', '.join(response.sources[:3])}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


def print_help():
    """Print example questions."""
    print("\n" + "=" * 50)
    print("📖 EXAMPLE QUESTIONS")
    print("=" * 50)
    
    print("\n💡 TIP: Try asking follow-up questions!")
    print("   The chatbot remembers your conversation.\n")
    
    examples = [
        ("First, ask about a topic:", [
            "Why did we choose React?",
            "Tell me about ONBOARD-14",
        ]),
        ("Then, follow up:", [
            "Who made that decision?",
            "What commits are related to it?",
            "Tell me more about the alternatives",
        ]),
        ("Other questions:", [
            "What happened in Sprint 1?",
            "How do I set up the project?",
            "What has Marcus been working on?",
        ]),
    ]
    
    for category, questions in examples:
        print(f"\n{category}")
        for q in questions:
            print(f"  • {q}")
    
    print("\n" + "=" * 50)


# =========================================
# TEST FUNCTION
# =========================================

def test_chatbot():
    """Test the chatbot with sample queries including follow-ups."""
    print("=" * 60)
    print("CONVERSATIONAL CHATBOT TEST")
    print("=" * 60)
    
    bot = OnboardingChatbot(verbose=True)
    
    # Test conversation with follow-ups
    conversation = [
        "Why did we choose React?",
        "Who made that decision?",           # Follow-up - should understand "that decision"
        "What alternatives were considered?", # Another follow-up
        "Tell me about ONBOARD-14",          # New topic
        "What commits are related to it?",   # Follow-up - "it" = ONBOARD-14
    ]
    
    print("\n📝 Testing multi-turn conversation:\n")
    
    for i, query in enumerate(conversation, 1):
        print(f"\n{'='*60}")
        print(f"Turn {i}: {query}")
        print("-" * 60)
        
        response = bot.chat(query)
        
        print(f"\n📝 ANSWER:\n{response.answer[:400]}...")
        print(f"\n📊 Metadata:")
        print(f"   Intent: {response.intent}")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Entities: {response.entities}")
        print(f"   Turn: {response.conversation_turn}")
    
    print("\n" + "=" * 60)
    print(f"Conversation completed: {bot.get_conversation_length()} turns")
    print("=" * 60)


# =========================================
# ENTRY POINT
# =========================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_chatbot()
    else:
        run_interactive()
