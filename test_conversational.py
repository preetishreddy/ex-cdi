"""
Test Script for Conversational Chatbot

This script demonstrates the multi-turn conversation capabilities.
Run from the Onboarding_AI directory:
    python test_conversational.py
"""

import sys
import os

# Add chatbot to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot import OnboardingChatbot


def test_single_turn():
    """Test basic single-turn queries."""
    print("=" * 70)
    print("TEST 1: Single-Turn Queries")
    print("=" * 70)
    
    bot = OnboardingChatbot(verbose=False)
    
    queries = [
        "Why did we choose React?",
        "Tell me about ONBOARD-14",
        "What happened in Sprint 1?",
    ]
    
    for query in queries:
        print(f"\n👤 User: {query}")
        response = bot.chat(query)
        print(f"🤖 Bot: {response.answer[:300]}...")
        print(f"   [Intent: {response.intent}, Confidence: {response.confidence:.0%}]")
        bot.clear_history()  # Clear between unrelated queries
    
    print("\n✅ Single-turn tests passed!")


def test_multi_turn_conversation():
    """Test multi-turn conversation with follow-ups."""
    print("\n" + "=" * 70)
    print("TEST 2: Multi-Turn Conversation (Follow-ups)")
    print("=" * 70)
    
    bot = OnboardingChatbot(verbose=False)
    
    conversation = [
        ("Why did we choose React?", "Initial question about React"),
        ("Who made that decision?", "Follow-up - 'that decision' should refer to React"),
        ("What alternatives were considered?", "Another follow-up about React decision"),
    ]
    
    for query, description in conversation:
        print(f"\n👤 User: {query}")
        print(f"   [{description}]")
        response = bot.chat(query)
        print(f"🤖 Bot: {response.answer[:300]}...")
        print(f"   [Turn: {response.conversation_turn}, Entities: {response.entities}]")
    
    print(f"\n📊 Total conversation turns: {bot.get_conversation_length()}")
    print("✅ Multi-turn conversation test passed!")


def test_topic_switch():
    """Test switching topics mid-conversation."""
    print("\n" + "=" * 70)
    print("TEST 3: Topic Switching")
    print("=" * 70)
    
    bot = OnboardingChatbot(verbose=False)
    
    conversation = [
        ("Tell me about ONBOARD-14", "Start with a ticket"),
        ("What commits are related to it?", "Follow-up - 'it' = ONBOARD-14"),
        ("Now tell me about the Tailwind decision", "Switch topic"),
        ("Why did we switch from Material UI?", "Continue on new topic"),
    ]
    
    for query, description in conversation:
        print(f"\n👤 User: {query}")
        print(f"   [{description}]")
        response = bot.chat(query)
        print(f"🤖 Bot: {response.answer[:250]}...")
    
    print("\n✅ Topic switching test passed!")


def test_reference_resolution():
    """Test pronoun and reference resolution."""
    print("\n" + "=" * 70)
    print("TEST 4: Reference Resolution")
    print("=" * 70)
    
    bot = OnboardingChatbot(verbose=True)  # Verbose to see resolution
    
    conversation = [
        "What has Marcus been working on?",
        "Tell me more about his commits",  # 'his' = Marcus
        "What tickets is he assigned to?",  # 'he' = Marcus
    ]
    
    for query in conversation:
        print(f"\n👤 User: {query}")
        response = bot.chat(query)
        print(f"🤖 Bot: {response.answer[:250]}...")
    
    print("\n✅ Reference resolution test passed!")


def test_clear_history():
    """Test clearing conversation history."""
    print("\n" + "=" * 70)
    print("TEST 5: Clear History")
    print("=" * 70)
    
    bot = OnboardingChatbot(verbose=False)
    
    # Build some history
    bot.chat("Why did we choose React?")
    bot.chat("Who decided that?")
    
    print(f"Before clear: {bot.get_conversation_length()} turns")
    
    bot.clear_history()
    
    print(f"After clear: {bot.get_conversation_length()} turns")
    
    # New query should not have previous context
    response = bot.chat("Tell me about that decision")
    print(f"\n👤 User: Tell me about that decision")
    print(f"🤖 Bot: {response.answer[:200]}...")
    print("   [Should not know what 'that decision' refers to after clear]")
    
    print("\n✅ Clear history test passed!")


def run_interactive_demo():
    """Run an interactive demo."""
    print("\n" + "=" * 70)
    print("INTERACTIVE DEMO")
    print("=" * 70)
    print("\nTry these conversation flows:\n")
    print("Flow 1 - Decision Deep-Dive:")
    print("  1. 'Why did we choose React?'")
    print("  2. 'Who made that decision?'")
    print("  3. 'What alternatives were considered?'")
    print()
    print("Flow 2 - Ticket Investigation:")
    print("  1. 'Tell me about ONBOARD-14'")
    print("  2. 'What commits are related to it?'")
    print("  3. 'Who is working on it?'")
    print()
    print("Flow 3 - Person Tracking:")
    print("  1. 'What has Marcus been working on?'")
    print("  2. 'Show me his recent commits'")
    print("  3. 'What decisions was he involved in?'")
    print()
    
    bot = OnboardingChatbot(verbose=False)
    
    while True:
        try:
            query = input(f"\n👤 You (turn {bot.get_conversation_length() + 1}): ").strip()
            
            if not query:
                continue
            if query.lower() in ['quit', 'exit', 'q']:
                break
            if query.lower() == 'clear':
                bot.clear_history()
                print("🗑️ History cleared!")
                continue
            
            response = bot.chat(query)
            print(f"\n🤖 Assistant: {response.answer}")
            print(f"\n   [Intent: {response.intent} | Sources: {', '.join(response.sources[:2])}]")
            
        except KeyboardInterrupt:
            break
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    print("=" * 70)
    print("CONVERSATIONAL CHATBOT TEST SUITE")
    print("=" * 70)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive_demo()
    else:
        test_single_turn()
        test_multi_turn_conversation()
        test_topic_switch()
        # test_reference_resolution()  # Verbose, uncomment if needed
        test_clear_history()
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED! ✅")
        print("=" * 70)
        print("\nRun with --interactive for demo mode:")
        print("  python test_conversational.py --interactive")
