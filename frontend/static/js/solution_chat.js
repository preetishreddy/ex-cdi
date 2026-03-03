/* ============================================================
   EX-CDI — Solution Chat (Agentic Mode)
   ============================================================
   An AI-powered assistant panel that queries the knowledge base
   APIs to answer questions about the project — ticketing, code,
   meetings, decisions, and more.
   ============================================================ */

const Solution = (() => {
  // ── State ─────────────────────────────────────────────────
  let isOpen = false;
  let isThinking = false;
  let messages = [];
  let conversationId = Date.now();  let chatHistory = [];          // { id, title, messages[], ts }
  let historyOpen = false;
  // ── DOM refs (set after inject) ───────────────────────────
  let panel, fab, messagesEl, textarea, sendBtn, statusText, statusDot;

  // ── Suggested questions ───────────────────────────────────
  const SUGGESTIONS = [
    { icon: 'search', text: 'What decisions were made this sprint?' },
    { icon: 'git-commit', text: 'Show me recent commits and their changes' },
    { icon: 'users', text: 'Who is working on what right now?' },
    { icon: 'file-text', text: 'Summarize the latest meeting notes' },
  ];

  // ── Icons ─────────────────────────────────────────────────
  const ICONS = {
    sparkles: '<svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><line x1="12" y1="11" x2="12" y2="14"/><path d="M8 14h8"/></svg>',
    send: '<svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
    close: '<svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    clear: '<svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    search: '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    'git-commit': '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><line x1="1.05" y1="12" x2="7" y2="12"/><line x1="17.01" y1="12" x2="22.96" y2="12"/></svg>',
    users: '<svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    'file-text': '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
    user: '<svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    bot: '<svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="3"/><path d="M7 15h0"/><path d="M17 15h0"/><path d="M9 19h6"/></svg>',
    check: '<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>',
    loader: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg>',
    zap: '<svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    newchat: '<svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    history: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    edit: '<svg viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
    collapse: '<svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>',
  };

  // ── Inject DOM ────────────────────────────────────────────
  function inject() {
    // Collapsed tab (replaces FAB)
    const tabEl = document.createElement('div');
    tabEl.className = 'solution-collapsed-tab';
    tabEl.title = 'Open Solution AI (Ctrl+L)';
    tabEl.innerHTML = `${ICONS.sparkles}<span>Solution</span><div class="tab-dot"></div>`;
    tabEl.addEventListener('click', toggle);
    document.body.appendChild(tabEl);
    fab = tabEl;

    // Panel
    const panelEl = document.createElement('div');
    panelEl.className = 'solution-panel';
    panelEl.innerHTML = `
      <div class="solution-header">
        <div class="solution-header-icon">${ICONS.sparkles}</div>
        <div>
          <div class="solution-header-title">Solution <span>AI</span></div>
          <div class="solution-header-subtitle">agentic assistant</div>
        </div>
        <div class="solution-header-actions">
          <button class="solution-header-btn" id="solutionNewChatBtn" title="New chat">${ICONS.newchat}</button>
          <button class="solution-header-btn" id="solutionHistoryBtn" title="Previous chats">${ICONS.history}</button>
          <button class="solution-header-btn" id="solutionCloseBtn" title="Collapse panel">${ICONS.collapse}</button>
        </div>
      </div>
      <div class="solution-history-drawer" id="solutionHistoryDrawer">
        <div class="solution-history-header">Previous Chats</div>
        <div class="solution-history-list" id="solutionHistoryList"></div>
      </div>
      <div class="solution-status">
        <div class="solution-status-dot" id="solutionStatusDot"></div>
        <span id="solutionStatusText">Ready — connected to knowledge base</span>
      </div>
      <div class="solution-messages" id="solutionMessages"></div>
      <div class="solution-input-area">
        <div class="solution-input-wrap">
          <textarea class="solution-textarea" id="solutionTextarea" placeholder="Ask Solution anything about this project..." rows="1"></textarea>
          <button class="solution-send-btn" id="solutionSendBtn" disabled>${ICONS.send}</button>
        </div>
        <div class="solution-hint">
          <span><kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> new line</span>
          <span><kbd>Ctrl+L</kbd> toggle</span>
        </div>
      </div>
    `;
    document.body.appendChild(panelEl);
    panel = panelEl;

    // Cache refs
    messagesEl = document.getElementById('solutionMessages');
    textarea = document.getElementById('solutionTextarea');
    sendBtn = document.getElementById('solutionSendBtn');
    statusText = document.getElementById('solutionStatusText');
    statusDot = document.getElementById('solutionStatusDot');

    // Events
    document.getElementById('solutionCloseBtn').addEventListener('click', close);
    document.getElementById('solutionNewChatBtn').addEventListener('click', newChat);
    document.getElementById('solutionHistoryBtn').addEventListener('click', toggleHistory);
    sendBtn.addEventListener('click', handleSend);

    textarea.addEventListener('input', () => {
      autoGrow();
      sendBtn.disabled = !textarea.value.trim() || isThinking;
    });

    textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (textarea.value.trim() && !isThinking) handleSend();
      }
    });

    // Global keyboard shortcut
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
        e.preventDefault();
        toggle();
      }
      if (e.key === 'Escape' && isOpen) {
        close();
      }
    });

    showWelcome();
    loadHistory();

    // Restore chat panel state from localStorage
    if (localStorage.getItem('solutionChatOpen') === 'true') {
      open();
    }
  }

  // ── Auto-grow textarea ────────────────────────────────────
  function autoGrow() {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  }

  // ── Open / Close / Toggle ─────────────────────────────────
  function open() {
    isOpen = true;
    document.body.classList.add('solution-open');
    localStorage.setItem('solutionChatOpen', 'true');
    setTimeout(() => textarea.focus(), 350);
  }

  function close() {
    isOpen = false;
    document.body.classList.remove('solution-open');
    localStorage.setItem('solutionChatOpen', 'false');
  }

  function toggle() {
    isOpen ? close() : open();
  }

  // ── Welcome Screen ────────────────────────────────────────
  function showWelcome() {
    const suggestionsHtml = SUGGESTIONS.map(s => `
      <button class="solution-suggestion" onclick="Solution.askSuggestion('${escHtml(s.text)}')">
        ${ICONS[s.icon]}
        <span>${escHtml(s.text)}</span>
      </button>
    `).join('');

    messagesEl.innerHTML = `
      <div class="solution-welcome">
        <div class="solution-welcome-icon">${ICONS.sparkles}</div>
        <h3>Solution AI</h3>
        <p>Your agentic project assistant. I can search commits, tickets, meetings, decisions, and Confluence pages to answer your questions.</p>
        <div class="solution-suggestions">
          ${suggestionsHtml}
        </div>
      </div>
    `;
  }

  // ── Ask suggestion ────────────────────────────────────────
  function askSuggestion(text) {
    textarea.value = text;
    autoGrow();
    sendBtn.disabled = false;
    handleSend();
  }

  // ── Clear conversation ────────────────────────────────────
  function clearConversation() {
    messages = [];
    conversationId = Date.now();
    showWelcome();
    setStatus('ready');
  }
  // ── Chat History (localStorage) ──────────────────────
const HISTORY_KEY = 'solution_chat_history';
const MAX_HISTORY = 20;

function loadHistory() {
  try {
    chatHistory = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
  } catch { chatHistory = []; }
}

function saveHistory() {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(chatHistory.slice(0, MAX_HISTORY)));
  } catch {}
}

function saveCurrentChat() {
  if (!messages.length) return;
  // Derive title from first user message
  const firstUser = messages.find(m => m.role === 'user');
  const title = firstUser ? firstUser.content.substring(0, 50) + (firstUser.content.length > 50 ? '…' : '') : 'Chat';

  // Update existing or create new
  const existing = chatHistory.findIndex(c => c.id === conversationId);
  const entry = { id: conversationId, title, messages: messages.slice(), ts: Date.now() };
  if (existing >= 0) {
    chatHistory[existing] = entry;
  } else {
    chatHistory.unshift(entry);
  }
  // Trim
  chatHistory = chatHistory.slice(0, MAX_HISTORY);
  saveHistory();
}

function newChat() {
  saveCurrentChat();
  messages = [];
  conversationId = Date.now();
  showWelcome();
  setStatus('ready');
  closeHistory();
}

function loadChat(id) {
  saveCurrentChat();
  const chat = chatHistory.find(c => c.id === id);
  if (!chat) return;
  conversationId = chat.id;
  messages = chat.messages.slice();
  // Re-render all messages
  messagesEl.innerHTML = '';
  messages.forEach((msg, idx) => {
    const div = document.createElement('div');
    div.className = 'msg';
    div.dataset.msgIndex = idx;
    div.innerHTML = `
      <div class="msg-avatar ${msg.role === 'user' ? 'user' : 'bot'}">
        ${msg.role === 'user' ? ICONS.user : ICONS.bot}
      </div>
      <div class="msg-body">
        <div class="msg-sender ${msg.role === 'user' ? 'user-name' : 'bot-name'}">${msg.role === 'user' ? 'You' : 'Solution'}</div>
        <div class="msg-content">${msg.role === 'user' ? escHtml(msg.content) : msg.content}</div>
        <div class="msg-time">${msg.time || ''}</div>
      </div>
      ${msg.role === 'user' ? `<button class="msg-edit-btn" onclick="Solution.editMessage(${idx})" title="Edit">${ICONS.edit}</button>` : ''}
    `;
    messagesEl.appendChild(div);
  });
  scrollToBottom();
  setStatus('ready');
  closeHistory();
}

function deleteChat(id, e) {
  e.stopPropagation();
  chatHistory = chatHistory.filter(c => c.id !== id);
  saveHistory();
  renderHistoryList();
}

function toggleHistory() {
  historyOpen ? closeHistory() : openHistory();
}

function openHistory() {
  historyOpen = true;
  renderHistoryList();
  document.getElementById('solutionHistoryDrawer').classList.add('open');
  document.getElementById('solutionHistoryBtn').classList.add('active');
}

function closeHistory() {
  historyOpen = false;
  document.getElementById('solutionHistoryDrawer').classList.remove('open');
  document.getElementById('solutionHistoryBtn').classList.remove('active');
}

function renderHistoryList() {
  const list = document.getElementById('solutionHistoryList');
  if (!chatHistory.length) {
    list.innerHTML = '<div class="solution-history-empty">No previous chats</div>';
    return;
  }
  list.innerHTML = chatHistory.map(c => {
    const date = new Date(c.ts);
    const when = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const msgCount = c.messages.filter(m => m.role === 'user').length;
    const isActive = c.id === conversationId;
    return `<div class="solution-history-item${isActive ? ' active' : ''}" onclick="Solution.loadChat(${c.id})">
      <div class="sh-item-body">
        <div class="sh-item-title">${escHtml(c.title)}</div>
        <div class="sh-item-meta">${when} · ${msgCount} message${msgCount !== 1 ? 's' : ''}</div>
      </div>
      <button class="sh-item-delete" onclick="Solution.deleteChat(${c.id}, event)" title="Delete">${ICONS.close}</button>
    </div>`;
  }).join('');
}
  // ── Handle Send ───────────────────────────────────────────
  async function handleSend() {
    const text = textarea.value.trim();
    if (!text || isThinking) return;

    // Remove welcome if present
    const welcome = messagesEl.querySelector('.solution-welcome');
    if (welcome) welcome.remove();

    // Add user message
    addMessage('user', text);
    saveCurrentChat();   // persist after each user message
    textarea.value = '';
    autoGrow();
    sendBtn.disabled = true;

    // Process
    await processQuery(text);
  }

  // ── Add message to UI ─────────────────────────────────────
  function addMessage(role, content, extras = {}) {
    const now = new Date();
    const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const msg = { role, content, time, ...extras };
    messages.push(msg);
    const msgIndex = messages.length - 1;
    saveCurrentChat();   // persist after bot response too

    const div = document.createElement('div');
    div.className = 'msg';
    div.dataset.msgIndex = msgIndex;
    div.innerHTML = `
      <div class="msg-avatar ${role === 'user' ? 'user' : 'bot'}">
        ${role === 'user' ? ICONS.user : ICONS.bot}
      </div>
      <div class="msg-body">
        <div class="msg-sender ${role === 'user' ? 'user-name' : 'bot-name'}">${role === 'user' ? 'You' : 'Solution'}</div>
        <div class="msg-content">${role === 'user' ? escHtml(content) : content}</div>
        ${extras.steps ? renderSteps(extras.steps) : ''}
        ${extras.results ? renderResults(extras.results) : ''}
        <div class="msg-time">${time}</div>
      </div>
      ${role === 'user' ? `<button class="msg-edit-btn" onclick="Solution.editMessage(${msgIndex})" title="Edit">${ICONS.edit}</button>` : ''}
    `;
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
  }

  // ── Thinking indicator ────────────────────────────────────
  function showThinking() {
    isThinking = true;
    sendBtn.disabled = true;
    setStatus('thinking');

    const div = document.createElement('div');
    div.className = 'msg';
    div.id = 'solutionThinking';
    div.innerHTML = `
      <div class="msg-avatar bot">${ICONS.bot}</div>
      <div class="msg-body">
        <div class="msg-sender bot-name">Solution</div>
        <div class="msg-steps" id="solutionSteps"></div>
        <div class="msg-thinking">
          <div class="msg-thinking-dot"></div>
          <div class="msg-thinking-dot"></div>
          <div class="msg-thinking-dot"></div>
        </div>
      </div>
    `;
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
  }

  function hideThinking() {
    isThinking = false;
    sendBtn.disabled = !textarea.value.trim();
    setStatus('ready');
    const el = document.getElementById('solutionThinking');
    if (el) el.remove();
  }

  function addStep(text, status = 'active') {
    const stepsEl = document.getElementById('solutionSteps');
    if (!stepsEl) return;

    // Complete previous active step
    const prev = stepsEl.querySelector('.msg-step.active');
    if (prev) {
      prev.classList.remove('active');
      prev.classList.add('done');
      prev.querySelector('.msg-step-icon').innerHTML = ICONS.check;
    }

    const step = document.createElement('div');
    step.className = `msg-step ${status}`;
    step.innerHTML = `
      <div class="msg-step-icon">${status === 'done' ? ICONS.check : ICONS.zap}</div>
      <span>${escHtml(text)}</span>
    `;
    stepsEl.appendChild(step);
    scrollToBottom();
  }

  function completeAllSteps() {
    const stepsEl = document.getElementById('solutionSteps');
    if (!stepsEl) return;
    stepsEl.querySelectorAll('.msg-step.active').forEach(s => {
      s.classList.remove('active');
      s.classList.add('done');
      s.querySelector('.msg-step-icon').innerHTML = ICONS.check;
    });
  }

  // ── Status ────────────────────────────────────────────────
  function setStatus(state) {
    if (state === 'thinking') {
      statusDot.classList.add('thinking');
      statusText.textContent = 'Thinking...';
    } else {
      statusDot.classList.remove('thinking');
      statusText.textContent = 'Ready — connected to knowledge base';
    }
  }

  // ── Process Query (Agentic Flow) ──────────────────────────
  async function processQuery(query) {
    const thinkingEl = showThinking();
    const lowerQ = query.toLowerCase();

    try {
      // Determine intent & run agentic steps
      const intent = classifyIntent(lowerQ);
      let responseHtml = '';
      let results = [];

      // Step 1: Parse intent
      addStep('Analyzing your question...');
      await delay(400);

      // Step 2: Choose data sources
      addStep(`Querying ${intent.sources.join(', ')}...`);
      await delay(200);

      // Step 3: Fetch data based on intent
      const apiData = await fetchForIntent(intent, query);

      // Step 4: Format response
      addStep('Formatting response...');
      await delay(300);

      const formatted = formatResponse(intent, apiData, query);
      responseHtml = formatted.html;
      results = formatted.results;

      completeAllSteps();
      hideThinking();

      addMessage('bot', responseHtml, { results });

    } catch (err) {
      console.error('Solution error:', err);
      completeAllSteps();
      hideThinking();
      addMessage('bot', `<p>Sorry, I ran into an error while processing your question.</p><p><code>${escHtml(err.message)}</code></p><p>Make sure the backend server is running and try again.</p>`);
    }
  }

  // ── Intent Classification ─────────────────────────────────
  function classifyIntent(q) {
    if (/decision|decided|chose|choice|rationale/.test(q)) {
      return { type: 'decisions', sources: ['decisions'] };
    }
    if (/commit|push|code change|merged|git|diff/.test(q)) {
      return { type: 'commits', sources: ['commits'] };
    }
    if (/ticket|issue|jira|bug|story|task|backlog/.test(q)) {
      return { type: 'tickets', sources: ['tickets'] };
    }
    if (/meeting|standup|sync|retro|call|discuss/.test(q)) {
      return { type: 'meetings', sources: ['meetings'] };
    }
    if (/confluence|page|doc|wiki|documentation/.test(q)) {
      return { type: 'pages', sources: ['pages'] };
    }
    if (/sprint|iteration|velocity|milestone/.test(q)) {
      return { type: 'sprints', sources: ['sprints'] };
    }
    if (/who|team|member|employee|engineer|assign/.test(q)) {
      return { type: 'employees', sources: ['employees'] };
    }
    if (/project|overview|status|summary|health/.test(q)) {
      return { type: 'project', sources: ['projects', 'sprints'] };
    }
    // Default: full-text search
    return { type: 'search', sources: ['search'] };
  }

  // ── Fetch for Intent ──────────────────────────────────────
  async function fetchForIntent(intent, query) {
    const base = '/api';

    switch (intent.type) {
      case 'decisions': {
        const res = await fetch(`${base}/decisions/`);
        return { decisions: await res.json() };
      }
      case 'commits': {
        const res = await fetch(`${base}/commits/`);
        return { commits: await res.json() };
      }
      case 'tickets': {
        const res = await fetch(`${base}/tickets/`);
        return { tickets: await res.json() };
      }
      case 'meetings': {
        const res = await fetch(`${base}/meetings/`);
        return { meetings: await res.json() };
      }
      case 'pages': {
        const res = await fetch(`${base}/pages/`);
        return { pages: await res.json() };
      }
      case 'sprints': {
        const res = await fetch(`${base}/sprints/`);
        return { sprints: await res.json() };
      }
      case 'employees': {
        const res = await fetch(`${base}/employees/`);
        return { employees: await res.json() };
      }
      case 'project': {
        const [projRes, sprintRes] = await Promise.all([
          fetch(`${base}/projects/`),
          fetch(`${base}/sprints/`),
        ]);
        return {
          projects: await projRes.json(),
          sprints: await sprintRes.json(),
        };
      }
      case 'search':
      default: {
        // Extract meaningful search terms
        const searchQ = extractSearchTerms(query);
        const res = await fetch(`${base}/search/?q=${encodeURIComponent(searchQ)}`);
        return { search: await res.json() };
      }
    }
  }

  function extractSearchTerms(q) {
    const stopwords = new Set(['what', 'is', 'the', 'a', 'an', 'how', 'do', 'does', 'did', 'can', 'show', 'me', 'tell', 'about', 'find', 'get', 'list', 'all', 'any', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'this', 'that', 'it', 'my', 'our', 'their', 'i', 'we', 'you', 'they', 'please', 'could', 'would', 'should']);
    const words = q.toLowerCase().replace(/[^\w\s-]/g, '').split(/\s+/).filter(w => !stopwords.has(w) && w.length > 1);
    return words.join(' ') || q;
  }

  // ── Format Response ───────────────────────────────────────
  function formatResponse(intent, data, query) {
    let html = '';
    let results = [];

    switch (intent.type) {
      case 'decisions': {
        const items = toArray(data.decisions);
        if (!items.length) {
          html = '<p>No decisions found in the knowledge base yet.</p>';
          break;
        }
        const recent = items.slice(0, 8);
        html = `<p>Found <strong>${items.length} decision${items.length !== 1 ? 's' : ''}</strong> in the knowledge base. Here are the most recent:</p>`;
        results = recent.map(d => ({
          type: 'Decision',
          title: d.title || d.summary || 'Untitled',
          meta: `${d.category || 'general'} · ${d.source_type || 'unknown'} · ${fmtDate(d.decided_at || d.created_at)}`,
        }));
        break;
      }

      case 'commits': {
        const items = toArray(data.commits);
        if (!items.length) {
          html = '<p>No commits found in the knowledge base.</p>';
          break;
        }
        const recent = items.slice(0, 8);
        html = `<p>Found <strong>${items.length} commit${items.length !== 1 ? 's' : ''}</strong>. Here are the latest:</p>`;
        results = recent.map(c => ({
          type: 'Commit',
          title: `${c.sha?.substring(0, 7) || '???'} — ${truncate(c.message, 80)}`,
          meta: `${c.author_name || 'Unknown'} · ${fmtDate(c.commit_date)}`,
        }));
        break;
      }

      case 'tickets': {
        const items = toArray(data.tickets);
        if (!items.length) {
          html = '<p>No Jira tickets found in the knowledge base.</p>';
          break;
        }
        const recent = items.slice(0, 8);
        html = `<p>Found <strong>${items.length} ticket${items.length !== 1 ? 's' : ''}</strong>. Here are the latest:</p>`;
        results = recent.map(t => ({
          type: t.issue_type || 'Ticket',
          title: `${t.issue_key} — ${truncate(t.summary, 80)}`,
          meta: `${t.status || 'unknown'} · ${t.assignee || 'Unassigned'} · ${t.priority || ''}`,
        }));
        break;
      }

      case 'meetings': {
        const items = toArray(data.meetings);
        if (!items.length) {
          html = '<p>No meetings found in the knowledge base.</p>';
          break;
        }
        const recent = items.slice(0, 6);
        html = `<p>Found <strong>${items.length} meeting${items.length !== 1 ? 's' : ''}</strong>. Here are the most recent:</p>`;
        results = recent.map(m => ({
          type: 'Meeting',
          title: m.title || 'Untitled meeting',
          meta: `${fmtDate(m.meeting_date)} · ${m.participants ? m.participants.split(',').length + ' participants' : ''}`,
        }));
        break;
      }

      case 'pages': {
        const items = toArray(data.pages);
        if (!items.length) {
          html = '<p>No Confluence pages found.</p>';
          break;
        }
        const recent = items.slice(0, 6);
        html = `<p>Found <strong>${items.length} page${items.length !== 1 ? 's' : ''}</strong>:</p>`;
        results = recent.map(p => ({
          type: 'Page',
          title: p.title || 'Untitled',
          meta: `${fmtDate(p.last_updated || p.created_at)}`,
        }));
        break;
      }

      case 'sprints': {
        const items = toArray(data.sprints);
        if (!items.length) {
          html = '<p>No sprints found.</p>';
          break;
        }
        html = `<p>Found <strong>${items.length} sprint${items.length !== 1 ? 's' : ''}</strong>:</p>`;
        results = items.slice(0, 8).map(s => ({
          type: `Sprint ${s.sprint_number || ''}`,
          title: s.name || `Sprint ${s.sprint_number}`,
          meta: `${s.status || 'unknown'} · ${fmtDate(s.start_date)} → ${fmtDate(s.end_date)}`,
        }));
        break;
      }

      case 'employees': {
        const items = toArray(data.employees);
        if (!items.length) {
          html = '<p>No team members found.</p>';
          break;
        }
        html = `<p>Found <strong>${items.length} team member${items.length !== 1 ? 's' : ''}</strong>:</p>`;
        results = items.map(e => ({
          type: 'Member',
          title: e.name || e.email || 'Unknown',
          meta: `${e.role || 'Employee'} · ${e.email || ''}`,
        }));
        break;
      }

      case 'project': {
        const projects = toArray(data.projects);
        const sprints = toArray(data.sprints);
        if (!projects.length) {
          html = '<p>No projects found in the knowledge base.</p>';
          break;
        }
        const p = projects[0];
        const activeSprints = sprints.filter(s => ['active', 'current', 'in_progress'].includes((s.status || '').toLowerCase()));
        const completedSprints = sprints.filter(s => ['completed', 'closed', 'done'].includes((s.status || '').toLowerCase()));

        html = `<p><strong>${escHtml(p.name || 'Project')}</strong></p>`;
        if (p.description) html += `<p>${escHtml(p.description)}</p>`;
        html += `<p>📊 <strong>${sprints.length}</strong> total sprints · <strong>${activeSprints.length}</strong> active · <strong>${completedSprints.length}</strong> completed</p>`;

        results = sprints.slice(0, 5).map(s => ({
          type: `Sprint`,
          title: s.name || `Sprint ${s.sprint_number}`,
          meta: `${s.status || 'unknown'} · ${fmtDate(s.start_date)} → ${fmtDate(s.end_date)}`,
        }));
        break;
      }

      case 'search':
      default: {
        const s = data.search || {};
        const commits = toArray(s.commits);
        const tickets = toArray(s.tickets);
        const pages = toArray(s.pages);
        const meetings = toArray(s.meetings);
        const total = commits.length + tickets.length + pages.length + meetings.length;

        if (total === 0) {
          html = `<p>No results found for <strong>"${escHtml(query)}"</strong>. Try different keywords or ask about a specific topic like commits, meetings, or decisions.</p>`;
          break;
        }

        html = `<p>Found <strong>${total} result${total !== 1 ? 's' : ''}</strong> for <strong>"${escHtml(query)}"</strong>:</p>`;

        commits.slice(0, 3).forEach(c => results.push({
          type: 'Commit',
          title: `${c.sha?.substring(0, 7)} — ${truncate(c.message, 70)}`,
          meta: `${c.author_name || ''} · ${fmtDate(c.commit_date)}`,
        }));
        tickets.slice(0, 3).forEach(t => results.push({
          type: 'Ticket',
          title: `${t.issue_key} — ${truncate(t.summary, 70)}`,
          meta: `${t.status || ''} · ${t.assignee || ''}`,
        }));
        pages.slice(0, 3).forEach(p => results.push({
          type: 'Page',
          title: p.title || 'Untitled',
          meta: fmtDate(p.last_updated || p.created_at),
        }));
        meetings.slice(0, 3).forEach(m => results.push({
          type: 'Meeting',
          title: m.title || 'Untitled',
          meta: fmtDate(m.meeting_date),
        }));
        break;
      }
    }

    return { html, results };
  }

  // ── Render Helpers ────────────────────────────────────────
  function renderSteps(steps) {
    return `<div class="msg-steps">${steps.map(s => `
      <div class="msg-step done">
        <div class="msg-step-icon">${ICONS.check}</div>
        <span>${escHtml(s)}</span>
      </div>
    `).join('')}</div>`;
  }

  function renderResults(results) {
    if (!results.length) return '';
    return `<div class="msg-results">${results.map(r => `
      <div class="msg-result-card">
        <div class="msg-result-card-type">${escHtml(r.type)}</div>
        <div class="msg-result-card-title">${escHtml(r.title)}</div>
        <div class="msg-result-card-meta">${escHtml(r.meta)}</div>
      </div>
    `).join('')}</div>`;
  }

  // ── Utilities ─────────────────────────────────────────────
  function escHtml(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
  }

  function toArray(v) {
    if (Array.isArray(v)) return v;
    if (v && Array.isArray(v.results)) return v.results;
    if (v && typeof v === 'object' && !Array.isArray(v)) return [v];
    return [];
  }

  function truncate(s, n) {
    if (!s) return '';
    s = String(s);
    return s.length > n ? s.substring(0, n) + '...' : s;
  }

  function fmtDate(d) {
    if (!d) return '';
    try {
      const dt = new Date(d);
      return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch { return String(d); }
  }

  function delay(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  // ── Edit message ──────────────────────────────────────────
  function editMessage(index) {
    if (isThinking) return;
    const msg = messages[index];
    if (!msg || msg.role !== 'user') return;

    // Remove this message and everything after it from state
    messages = messages.slice(0, index);
    saveCurrentChat();

    // Remove the corresponding DOM elements
    const allMsgEls = messagesEl.querySelectorAll('.msg');
    for (let i = allMsgEls.length - 1; i >= 0; i--) {
      const elIdx = parseInt(allMsgEls[i].dataset.msgIndex, 10);
      if (elIdx >= index) allMsgEls[i].remove();
    }

    // If no messages left, show welcome
    if (!messages.length) showWelcome();

    // Put the text into the textarea for editing
    textarea.value = msg.content;
    autoGrow();
    sendBtn.disabled = false;
    textarea.focus();
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  // ── Public API ────────────────────────────────────────────
  return {
    init: inject,
    open,
    close,
    toggle,
    askSuggestion,
    loadChat,
    deleteChat,
    editMessage,
  };
})();

// ── Auto-initialize on DOM ready ────────────────────────────
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => Solution.init());
} else {
  Solution.init();
}
