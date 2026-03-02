# Onboarding AI Chatbot - Setup & Integration Guide

> **Version 2.0.0** - Conversational Chatbot with Memory

This guide is for backend developers and integrators who need to set up, run, and integrate the Onboarding AI Chatbot.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Chatbot](#running-the-chatbot)
7. [Conversation Features](#conversation-features)
8. [API Integration](#api-integration)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)
12. [Architecture Reference](#architecture-reference)

---

## Overview

The Onboarding AI Chatbot is a **conversational assistant** that helps team members understand the Employee Onboarding Portal project. It features multi-turn conversations with memory, allowing natural follow-up questions.

### Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **Conversation Memory** | Remembers previous messages in a session |
| 🔍 **Reference Resolution** | Understands "it", "that", "they" from context |
| 📊 **Intent Classification** | 8 query types with automatic detection |
| 🗄️ **Database Retrieval** | Direct PostgreSQL queries (no vector DB needed) |
| 🤖 **GPT-4o Responses** | Powered by Bytez API |

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Django 5.x |
| Database | PostgreSQL (Render) |
| LLM Provider | Bytez API (GPT-4o) |
| Language | Python 3.10+ |

### What It Can Answer

```
Decision Queries     → "Why did we choose React?" → "Who made that decision?"
Person Queries       → "What has Marcus been working on?" → "Show me his commits"
Ticket Queries       → "Tell me about ONBOARD-14" → "What's its status?"
Meeting Queries      → "What was discussed in Sprint 1 Planning?"
Setup Queries        → "How do I set up the project locally?"
Timeline Queries     → "What happened in Sprint 1?"
```

---

## Prerequisites

Before setting up the chatbot, ensure you have:

- [ ] Python 3.10 or higher
- [ ] Access to the project repository
- [ ] PostgreSQL database populated with project data
- [ ] Bytez API key (optional - default key available)

### Check Python Version

```bash
python --version
# Should be 3.10 or higher
```

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd Onboarding_AI

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the chatbot
cd chatbot
python main.py
```

---

## Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd Onboarding_AI
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
```
django>=5.0
psycopg2-binary
python-dotenv
bytez
```

### Step 4: Verify Installation

```bash
python -c "from chatbot import OnboardingChatbot; print('✓ Installation successful!')"
```

---

## Configuration

### Environment Variables

Create or verify `database/.env`:

```bash
# PostgreSQL Database (Render)
DATABASE_URL=postgresql://username:password@host:port/database_name

# Or individual settings
DB_NAME=project_knowledge
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host.render.com
DB_PORT=5432

# Bytez API Key (for GPT-4o)
BYTEZ_API_KEY=your_api_key_here
```

### Database Connection

Verify the database connection:

```bash
cd database
python manage.py shell
```

```python
from knowledge_base.models import Decision
print(f"Decisions in DB: {Decision.objects.count()}")
# Should show a number > 0
```

### Bytez API Key

Options:
1. **Use default key** - Hardcoded fallback for development
2. **Set your own key** - Add `BYTEZ_API_KEY` to `.env`

Get an API key at: https://bytez.com

---

## Running the Chatbot

### Interactive Mode (CLI)

```bash
cd ~/Desktop/Onboarding_AI/chatbot
source ../venv/bin/activate
python main.py
```

**CLI Commands:**

| Command | Description |
|---------|-------------|
| `quit` | Exit the chatbot |
| `help` | Show example questions |
| `clear` | Clear conversation history |
| `debug` | Toggle verbose/debug mode |

### Example Session

```
============================================================
🤖 ONBOARDING AI CHATBOT (Conversational)
============================================================

Welcome! I remember our conversation, so feel free to ask follow-up questions!

👤 You (turn 1): Why did we choose React?

🤖 Assistant: React was chosen for the frontend during Sprint 1 Planning 
on January 6, 2026. The decision was made by Sarah Chen and Lisa Park.

Key reasons:
- Component-based architecture for reusable UI elements
- Team expertise with React
- Strong community support

Alternatives considered: Vue, Angular

   📊 Intent: decision_query | Confidence: 85%
   📚 Sources: decision:Use React for frontend

👤 You (turn 2): Who made that decision?

🤖 Assistant: The React decision was made by Sarah Chen and Lisa Park,
as documented in ticket ONBOARD-13.

   📊 Intent: decision_query | Confidence: 80%
   📚 Sources: decision:Use React for frontend

👤 You (turn 3): What alternatives were considered?

🤖 Assistant: For the frontend framework decision, the alternatives 
considered were Vue and Angular. React was preferred due to its 
component-based architecture and the team's existing expertise.

   📊 Intent: decision_query | Confidence: 82%
   📚 Sources: decision:Use React for frontend
```

### Test Mode

```bash
python main.py --test
```

Runs automated tests including multi-turn conversation tests.

### Conversational Test Suite

```bash
cd ~/Desktop/Onboarding_AI
python test_conversational.py              # Run all tests
python test_conversational.py --interactive # Interactive demo
```

---

## Conversation Features

### Multi-Turn Memory

The chatbot remembers up to 10 previous exchanges:

```python
bot = OnboardingChatbot()

# Turn 1
bot.chat("Why did we choose React?")

# Turn 2 - Bot remembers React context
bot.chat("Who made that decision?")  # Knows "that" = React decision

# Turn 3 - Still has context
bot.chat("What alternatives were considered?")
```

### Reference Resolution

The bot resolves pronouns and references:

| User Says | Bot Understands |
|-----------|-----------------|
| "Tell me more about it" | "Tell me more about [last topic]" |
| "Who made that decision?" | "Who made the React decision?" |
| "What's its status?" | "What's ONBOARD-14's status?" |
| "Show me his commits" | "Show me Marcus's commits" |

### Clearing History

```python
# In code
bot.clear_history()

# In CLI
# Type: clear
```

### Checking Conversation State

```python
bot.get_conversation_length()  # Returns number of turns
bot.health_check()             # Returns component status
```

---

## API Integration

### Programmatic Usage

```python
from chatbot import OnboardingChatbot

# Initialize
bot = OnboardingChatbot(verbose=False)

# Simple usage - just get the answer
answer = bot.chat_simple("Why did we choose React?")
print(answer)

# Full usage - get structured response
response = bot.chat("Why did we choose React?")
print(f"Answer: {response.answer}")
print(f"Intent: {response.intent}")
print(f"Confidence: {response.confidence}")
print(f"Sources: {response.sources}")
print(f"Turn: {response.conversation_turn}")

# Follow-up (bot remembers context)
response = bot.chat("Who made that decision?")
print(response.answer)

# Clear history when starting new topic
bot.clear_history()
```

### ChatResponse Object

```python
@dataclass
class ChatResponse:
    answer: str              # The generated response
    intent: str              # Classified intent type
    confidence: float        # Classification confidence (0-1)
    sources: List[str]       # Sources used for answer
    entities: List[str]      # Extracted/carried entities
    conversation_turn: int   # Current turn number
```

### Flask Integration

```python
from flask import Flask, request, jsonify, session
from chatbot import OnboardingChatbot

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Store bots per session
chatbots = {}

def get_bot(session_id):
    if session_id not in chatbots:
        chatbots[session_id] = OnboardingChatbot()
    return chatbots[session_id]

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query', '')
    session_id = session.get('id', 'default')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    bot = get_bot(session_id)
    response = bot.chat(query)
    
    return jsonify({
        'answer': response.answer,
        'intent': response.intent,
        'confidence': response.confidence,
        'sources': response.sources,
        'turn': response.conversation_turn
    })

@app.route('/api/clear', methods=['POST'])
def clear_history():
    session_id = session.get('id', 'default')
    bot = get_bot(session_id)
    bot.clear_history()
    return jsonify({'status': 'cleared'})

@app.route('/api/health', methods=['GET'])
def health():
    bot = OnboardingChatbot()
    return jsonify(bot.health_check())

if __name__ == '__main__':
    app.run(port=5000)
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from chatbot import OnboardingChatbot

app = FastAPI()

# In-memory session storage (use Redis for production)
sessions = {}

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    sources: List[str]
    entities: List[str]
    turn: int

def get_bot(session_id: str) -> OnboardingChatbot:
    if session_id not in sessions:
        sessions[session_id] = OnboardingChatbot()
    return sessions[session_id]

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    bot = get_bot(request.session_id)
    response = bot.chat(request.query)
    
    return ChatResponse(
        answer=response.answer,
        intent=response.intent,
        confidence=response.confidence,
        sources=response.sources,
        entities=response.entities,
        turn=response.conversation_turn
    )

@app.post("/clear/{session_id}")
async def clear_history(session_id: str):
    if session_id in sessions:
        sessions[session_id].clear_history()
    return {"status": "cleared"}

@app.get("/health")
async def health():
    bot = OnboardingChatbot()
    return bot.health_check()
```

### React Frontend Integration

```javascript
// ChatComponent.jsx
import React, { useState, useRef, useEffect } from 'react';

function ChatComponent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input })
      });
      
      const data = await res.json();
      
      const botMessage = {
        role: 'assistant',
        content: data.answer,
        meta: {
          intent: data.intent,
          confidence: data.confidence,
          sources: data.sources,
          turn: data.turn
        }
      };
      
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, something went wrong.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    await fetch('/api/clear', { method: 'POST' });
    setMessages([]);
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <p>{msg.content}</p>
            {msg.meta && (
              <small>
                Intent: {msg.meta.intent} | 
                Turn: {msg.meta.turn}
              </small>
            )}
          </div>
        ))}
        {loading && <div className="loading">Thinking...</div>}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={sendMessage}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about the project..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>Send</button>
        <button type="button" onClick={clearHistory}>Clear</button>
      </form>
    </div>
  );
}

export default ChatComponent;
```

---

## Testing

### Run All Module Tests

```bash
cd ~/Desktop/Onboarding_AI/chatbot

# Test intent classifier
python -m intent.classifier

# Test retriever
python -m retriever.sql_retriever

# Test context builder
python -m context.builder

# Test LLM
python -m llm.bytez_llm

# Test full chatbot
python main.py --test
```

### Run Conversational Tests

```bash
cd ~/Desktop/Onboarding_AI
python test_conversational.py
```

Tests include:
- Single-turn queries
- Multi-turn conversations with follow-ups
- Topic switching
- Reference resolution
- History clearing

### Test Specific Conversations

```python
from chatbot import OnboardingChatbot

bot = OnboardingChatbot(verbose=True)  # See debug output

# Test conversation flow
conversations = [
    # Flow 1: Decision deep-dive
    ["Why did we choose React?", "Who made that decision?", "What alternatives?"],
    
    # Flow 2: Ticket investigation
    ["Tell me about ONBOARD-14", "What commits relate to it?", "Who's working on it?"],
    
    # Flow 3: Person tracking
    ["What has Marcus been working on?", "Show me his commits", "What decisions was he in?"],
]

for convo in conversations:
    print(f"\n{'='*50}")
    bot.clear_history()
    for query in convo:
        response = bot.chat(query)
        print(f"Q: {query}")
        print(f"A: {response.answer[:150]}...")
        print()
```

### Health Check

```python
from chatbot import OnboardingChatbot

bot = OnboardingChatbot()
health = bot.health_check()

print("Component Status:")
for component, status in health.items():
    if isinstance(status, dict):
        print(f"  {component}: {status['status']}")
    else:
        print(f"  {component}: {status}")
```

---

## Deployment

### Option 1: Systemd Service

Create `/etc/systemd/system/chatbot-api.service`:

```ini
[Unit]
Description=Onboarding AI Chatbot API
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/Onboarding_AI
Environment=PATH=/opt/Onboarding_AI/venv/bin
ExecStart=/opt/Onboarding_AI/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 api:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable chatbot-api
sudo systemctl start chatbot-api
```

### Option 2: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "api:app"]
```

```bash
docker build -t onboarding-chatbot .
docker run -p 5000:5000 --env-file database/.env onboarding-chatbot
```

### Option 3: AWS Lambda

```python
# lambda_handler.py
import json
from chatbot import OnboardingChatbot

# Store bots per connection (use DynamoDB for persistence)
bots = {}

def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    query = body.get('query', '')
    session_id = body.get('session_id', 'default')
    
    if not query:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No query provided'})
        }
    
    # Get or create bot for session
    if session_id not in bots:
        bots[session_id] = OnboardingChatbot()
    
    bot = bots[session_id]
    response = bot.chat(query)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'answer': response.answer,
            'intent': response.intent,
            'confidence': response.confidence,
            'turn': response.conversation_turn
        })
    }
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: django` | Venv not activated | `source venv/bin/activate` |
| `ModuleNotFoundError: chatbot` | Wrong directory | `cd Onboarding_AI` |
| Database connection error | Missing `.env` | Check `database/.env` |
| LLM not responding | API key issue | Verify `BYTEZ_API_KEY` |
| Wrong intent detected | Keyword mismatch | Check `intent/types.py` |
| No results returned | Empty database | Verify data exists |
| "I don't know" responses | Context not found | Check retriever queries |

### Debug Mode

Enable verbose output to trace issues:

```python
bot = OnboardingChatbot(verbose=True)
response = bot.chat("Why did we choose React?")
```

Output shows:
- Resolved query (if references resolved)
- Intent classification details
- Documents retrieved
- Context length
- Response generation

### Check Database Content

```bash
cd database
python manage.py shell
```

```python
from knowledge_base.models import Decision, Meeting, JiraTicket

print(f"Decisions: {Decision.objects.count()}")
print(f"Meetings: {Meeting.objects.count()}")
print(f"Tickets: {JiraTicket.objects.count()}")

# Check specific content
for d in Decision.objects.all()[:5]:
    print(f"  - {d.title}")
```

### Check Intent Classification

```python
from chatbot.intent import IntentClassifier

classifier = IntentClassifier()
result, explanation = classifier.classify_with_explanation("Your query here")
print(explanation)
```

---

## Architecture Reference

### Project Structure

```
Onboarding_AI/
├── chatbot/                    # Chatbot application
│   ├── __init__.py
│   ├── main.py                 # Main + ConversationHistory
│   ├── django_setup.py         # Django configuration
│   ├── README.md               # Technical documentation
│   │
│   ├── intent/                 # Intent classification
│   │   ├── types.py            # IntentType enum
│   │   └── classifier.py       # Classification logic
│   │
│   ├── retriever/              # Data retrieval
│   │   ├── base.py             # Document class
│   │   └── sql_retriever.py    # PostgreSQL queries
│   │
│   ├── context/                # Context building
│   │   ├── templates.py        # Prompt templates
│   │   └── builder.py          # Context formatting
│   │
│   └── llm/                    # LLM interface
│       └── bytez_llm.py        # Bytez API wrapper
│
├── database/                   # Django project
│   ├── config/                 # Settings
│   ├── knowledge_base/         # Models
│   └── .env                    # Environment variables
│
├── docs/                       # Documentation
│   └── CHATBOT_SETUP_GUIDE.md  # This file
│
├── test_conversational.py      # Conversation tests
├── venv/                       # Virtual environment
└── requirements.txt            # Dependencies
```

### Database Tables

| Table | Purpose |
|-------|---------|
| `decisions` | Project decisions with rationale |
| `meetings` | Meeting summaries and key points |
| `jira_tickets` | Tickets with status and comments |
| `confluence_pages` | Documentation content |
| `git_commits` | Commit history |
| `employees` | Team member info |

### Intent Types

| Intent | Keywords | Tables |
|--------|----------|--------|
| `decision_query` | why, decision, chose | decisions, meetings |
| `person_query` | who, worked, assigned | employees, tickets, commits |
| `timeline_query` | when, sprint, history | decisions, sprints |
| `howto_query` | how, setup, configure | confluence_pages |
| `status_query` | status, progress, done | jira_tickets |
| `ticket_query` | ONBOARD-XX, ticket | jira_tickets, commits |
| `meeting_query` | meeting, discussed | meetings |
| `general_query` | (fallback) | all tables |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Jan 2026 | Initial release - Single-turn Q&A |
| 2.0.0 | Jan 2026 | Conversational - Multi-turn with memory |

---

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review technical docs in `chatbot/README.md`
3. Run tests: `python test_conversational.py`
4. Contact the development team

---

## Next Steps

After testing, provide feedback on:

1. **Intent Detection Issues** - Queries classified incorrectly
2. **Missing Entities** - Terms not being extracted
3. **Response Quality** - Answers that could be improved
4. **New Question Types** - Queries the bot should handle

This feedback will be used to enhance:
- Intent keywords in `intent/types.py`
- Prompt templates in `context/templates.py`
- Retrieval queries in `retriever/sql_retriever.py`
