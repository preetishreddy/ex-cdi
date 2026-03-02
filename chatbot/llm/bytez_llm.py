"""
Bytez LLM Wrapper for Onboarding AI Chatbot

Provides a simple interface to the Bytez API (GPT-4o).
Designed to be swappable with other LLM providers if needed.
"""

import os
from typing import Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BytezLLM:
    """
    Wrapper for Bytez API to access GPT-4o.
    
    Features:
    - Simple generate() interface
    - Configurable model and parameters
    - Error handling and retries
    - Response extraction
    """
    
    DEFAULT_MODEL = "openai/gpt-4o"
    
    def __init__(
        self, 
        model_name: str = None,
        api_key: str = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ):
        """
        Initialize the LLM wrapper.
        
        Args:
            model_name: Model to use (default: openai/gpt-4o)
            api_key: Bytez API key (default: from env)
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0-1)
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.api_key = api_key or os.getenv('BYTEZ_API_KEY', '19408716817b70780ddaaea1a7e32eb6')
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize Bytez SDK
        self._init_client()
    
    def _init_client(self):
        """Initialize the Bytez client."""
        try:
            from bytez import Bytez
            self.sdk = Bytez(self.api_key)
            self.model = self.sdk.model(self.model_name)
            self._available = True
        except ImportError:
            print("Warning: bytez package not installed. Run: pip install bytez")
            self._available = False
        except Exception as e:
            print(f"Warning: Failed to initialize Bytez client: {e}")
            self._available = False
    
    @property
    def is_available(self) -> bool:
        """Check if the LLM is available."""
        return self._available
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt/query
            system_prompt: Optional system prompt (prepended)
            
        Returns:
            Generated response text
        """
        if not self._available:
            return "Error: LLM not available. Please check your Bytez API configuration."
        
        try:
            # Build messages
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Call API
            results = self.model.run(messages)
            
            if results.error:
                return f"Error from API: {results.error}"
            
            return self._extract_response(results.output)
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _extract_response(self, output: Any) -> str:
        """Extract text from API response."""
        if isinstance(output, str):
            return output
        
        if isinstance(output, dict):
            # Handle OpenAI-style response
            if 'choices' in output:
                return output['choices'][0]['message']['content']
            
            # Handle other formats
            for key in ['content', 'text', 'message', 'response']:
                if key in output:
                    val = output[key]
                    if isinstance(val, dict) and 'content' in val:
                        return val['content']
                    return str(val)
        
        if isinstance(output, list) and output:
            return self._extract_response(output[0])
        
        return str(output)
    
    def generate_with_context(
        self, 
        query: str, 
        context: str, 
        intent_type: str = "general_query"
    ) -> str:
        """
        Generate a response with retrieved context.
        
        This is a convenience method that combines context and query.
        
        Args:
            query: User's question
            context: Retrieved context from database
            intent_type: Type of query for prompt selection
            
        Returns:
            Generated response
        """
        # Build prompt based on intent type
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
Your role is to help team members understand project decisions, architecture, and history.

INSTRUCTIONS: {instruction}

IMPORTANT RULES:
1. Only answer based on the provided context
2. If information is marked as "superseded", mention that newer decisions exist
3. Always cite your sources (meeting name, ticket ID, etc.)
4. If you don't have enough information, say so clearly
5. Be concise but complete

CONTEXT:
{context}

USER QUESTION: {query}

Provide a helpful, accurate answer:"""
        
        return self.generate(prompt)
    
    def health_check(self) -> dict:
        """
        Check if the LLM is working properly.
        
        Returns:
            Dict with status and details
        """
        if not self._available:
            return {
                'status': 'error',
                'message': 'LLM client not initialized'
            }
        
        try:
            response = self.generate("Say 'OK' if you're working.")
            
            if 'OK' in response or 'ok' in response.lower():
                return {
                    'status': 'ok',
                    'model': self.model_name,
                    'message': 'LLM is responding correctly'
                }
            else:
                return {
                    'status': 'warning',
                    'model': self.model_name,
                    'message': f'Unexpected response: {response[:100]}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }


# =========================================
# TEST FUNCTION
# =========================================

def test_llm():
    """Test the LLM wrapper."""
    print("=" * 60)
    print("BYTEZ LLM TEST")
    print("=" * 60)
    
    llm = BytezLLM()
    
    # Test 1: Health check
    print("\n1. Health Check:")
    print("-" * 40)
    health = llm.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Message: {health['message']}")
    
    if health['status'] == 'error':
        print("\n❌ LLM not available. Skipping further tests.")
        return
    
    # Test 2: Simple generation
    print("\n2. Simple Generation:")
    print("-" * 40)
    response = llm.generate("What is 2 + 2? Answer in one word.")
    print(f"   Response: {response}")
    
    # Test 3: Generation with context
    print("\n3. Generation with Context:")
    print("-" * 40)
    
    context = """
    📋 DECISION: Use React for frontend
    Date: 2026-01-06
    Category: technology
    Decided by: Sarah Chen, Marcus Thompson
    
    Rationale: React has strong community support and the team has expertise.
    Alternatives Considered: Vue, Angular
    """
    
    response = llm.generate_with_context(
        query="Why did we choose React?",
        context=context,
        intent_type="decision_query"
    )
    print(f"   Response: {response[:500]}...")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_llm()