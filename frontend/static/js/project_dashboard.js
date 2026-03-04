/* ============================================================
   EX-CDI — Project Overview JavaScript
   ============================================================ */

// ── Sprint Data (fetched from API) ───────────────────────────
let SPRINTS = [];

// ── Constants ────────────────────────────────────────────────
const MO = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// ── State ────────────────────────────────────────────────────
let activeSprint = null;
let decisionsLoaded = false;
let decisionsData = [];

// ── Global Tickets Cache (fetched once, reused everywhere) ───
let _ticketsCachePromise = null;
function fetchTicketsOnce() {
  if (!_ticketsCachePromise) {
    _ticketsCachePromise = fetch('/api/tickets/')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => Array.isArray(data) ? data : (data.results || []));
  }
  return _ticketsCachePromise;
}

// ── Auth Guard ───────────────────────────────────────────────
if (!sessionStorage.getItem('isLoggedIn')) {
  window.location.href = 'login.html';
}

// ── User Setup ───────────────────────────────────────────────
const userEmail = sessionStorage.getItem('userEmail') || 'user@company.atlassian.net';
const jiraDomain = sessionStorage.getItem('jiraDomain') || 'company.atlassian.net';
const userName = userEmail.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

document.getElementById('sidebarUserName').textContent = userName;
document.getElementById('userAvatar').textContent = userName.split(' ').map(w => w[0]).join('').substring(0, 2);

// ── Fetch Sprints from API ───────────────────────────────────
async function fetchSprints() {
  const res = await fetch('/api/sprints/');
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  const list = Array.isArray(data) ? data : (data.results || []);

  // Map API status values to frontend status keys
  function mapStatus(s) {
    if (!s) return 'upcoming';
    const lower = s.toLowerCase();
    if (['completed', 'closed', 'done'].includes(lower)) return 'completed';
    if (['active', 'current', 'in progress', 'in_progress'].includes(lower)) return 'current';
    return 'upcoming'; // planned, future, etc.
  }

  SPRINTS = list.map(sp => ({
    id: `s${sp.sprint_number}`,
    sprint_number: sp.sprint_number,
    name: sp.name,
    status: mapStatus(sp.status),
    dates: [sp.start_date, sp.end_date],
    goal: sp.goal || '',
    project: sp.project || null,
    meetings: [],            // loaded on-demand per sprint
    aiSummary: sp.goal
      ? `<strong>${esc(sp.name)}</strong> — ${esc(sp.goal)}`
      : `<strong>${esc(sp.name)}</strong> — Sprint backlog.`,
  }));

  return SPRINTS;
}

// ── Loading Animation & Init ─────────────────────────────────
(async function initDashboard() {
  const overlay = document.getElementById('loadingOverlay');
  const barFill = document.getElementById('loadingBarFill');
  const loadText = document.getElementById('loadingText');

  // Only show the loading animation on first visit after login
  const alreadyLoaded = sessionStorage.getItem('dashboardLoaded');

  // ── Fetch ALL data in parallel (sprints + projects + tickets) ──
  async function fetchAllData() {
    const [, , tickets] = await Promise.all([
      fetchSprints().catch(e => { console.error('Failed to fetch sprints:', e); }),
      loadProjectRail().catch(e => { console.error('Failed to load projects:', e); }),
      fetchTicketsOnce().catch(e => { console.error('Failed to fetch tickets:', e); return []; }),
    ]);
    // Populate the tickets cache so loadTickets / loadIgJira don't re-fetch
    if (tickets && tickets.length) {
      ticketsData = tickets;
      ticketsLoaded = true;
      igTicketsData = tickets;
    }
  }

  if (alreadyLoaded) {
    // Skip animation — just fetch data and render immediately
    overlay.remove();
    await fetchAllData();
    renderProjectGoal();
    renderProjectSummary();
    applyPageRouting();
    if (!isIntegrationsPage()) {
      document.getElementById('topbarSub').textContent = `${SPRINTS.length} sprints`;
      loadProjectTicketStats();
      buildTimeline();
      if (SPRINTS.length) {
        selectSprint((SPRINTS.find(s => s.status === 'current') || SPRINTS[0]).id);
      }
    }
    return;
  }

  sessionStorage.setItem('dashboardLoaded', '1');

  // Step 1 – animate bar
  setTimeout(() => { barFill.style.width = '30%'; loadText.textContent = 'Connecting to workspace...'; }, 300);
  setTimeout(() => { barFill.style.width = '55%'; loadText.textContent = 'Fetching sprints & projects...'; }, 900);

  // Step 2 – fetch ALL data in parallel while animation runs
  await fetchAllData();

  // Step 3 – finish bar
  setTimeout(() => { barFill.style.width = '85%'; loadText.textContent = 'Building dashboard...'; }, 1600);

  setTimeout(() => {
    barFill.style.width = '100%';
    loadText.textContent = 'Ready';
  }, 2200);

  // Step 4 – hide overlay & render
  setTimeout(() => {
    overlay.classList.add('hidden');
    renderProjectGoal();
    renderProjectSummary();
    applyPageRouting();
    if (!isIntegrationsPage()) {
      document.getElementById('topbarSub').textContent = `${SPRINTS.length} sprints`;
      loadProjectTicketStats();
      buildTimeline();
      if (SPRINTS.length) {
        selectSprint((SPRINTS.find(s => s.status === 'current') || SPRINTS[0]).id);
      }
    }
    // Remove overlay from DOM after transition
    setTimeout(() => overlay.remove(), 600);
  }, 2800);
})();

// ── Helpers ──────────────────────────────────────────────────
// Parse any date string as a *local* Date, extracting the calendar date
// from the string directly (no timezone shift).
// "2026-01-05T00:00:00Z" → local Date for Jan 5
// "2026-01-05"           → local Date for Jan 5
function localDate(s) {
  const str = String(s || '');
  // Always extract YYYY-MM-DD from the beginning of the string
  const match = str.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  }
  return new Date(str);
}
function localDateStr(s) {
  const str = String(s || '');
  // Fast path: extract YYYY-MM-DD directly from ISO strings
  const match = str.match(/^(\d{4}-\d{2}-\d{2})/);
  if (match) return match[1];
  const d = localDate(str);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function fmtR(s, e) {
  const a = localDate(s), b = localDate(e);
  return `${MO[a.getMonth()]} ${a.getDate()} – ${MO[b.getMonth()]} ${b.getDate()}`;
}

function ini(n) {
  return n.split(' ').map(w => w[0]).join('').substring(0, 2);
}

function gr(n) {
  const g = [
    'linear-gradient(135deg,#1e8fff,#6c5ce7)', 'linear-gradient(135deg,#f5a623,#ff6b6b)',
    'linear-gradient(135deg,#f5a623,#ff8c00)', 'linear-gradient(135deg,#00d48a,#1e8fff)',
    'linear-gradient(135deg,#e84393,#fd79a8)', 'linear-gradient(135deg,#6c5ce7,#a29bfe)'
  ];
  let h = 0;
  for (let i = 0; i < n.length; i++) h = n.charCodeAt(i) + ((h << 5) - h);
  return g[Math.abs(h) % g.length];
}

function rl(n, is) {
  const l = is.filter(i => i.assignee === n).flatMap(i => i.labels.split(';'));
  if (l.includes('frontend')) return 'Frontend';
  if (l.includes('ml')) return 'ML Engineer';
  if (l.includes('backend') || l.includes('auth')) return 'Backend';
  if (l.includes('database') || l.includes('devops') || l.includes('infrastructure')) return 'DevOps';
  return 'Engineer';
}

function pCl(s) {
  return s === 'Done' ? 'done' : s === 'Blocked' ? 'blocked' : s === 'In Review' ? 'review' : 'progress';
}

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = String(s);
  return d.innerHTML;
}

// ── Timeline ─────────────────────────────────────────────────
function buildTimeline() {
  const el = document.getElementById('timeline');
  document.getElementById('timelineWrap').classList.add('visible');
  const ci = SPRINTS.findIndex(s => s.status === 'current');
  const pct = ci >= 0
    ? ((ci + .5) / SPRINTS.length) * 100
    : (SPRINTS.filter(s => s.status === 'completed').length / SPRINTS.length) * 100;

  let h = `<div class="timeline-progress" style="width:${pct}%"></div>`;

  SPRINTS.forEach(sp => {
    const c = sp.status === 'completed' ? 'completed' : sp.status === 'current' ? 'current' : 'future';
    const t = sp.status === 'completed' ? 'done' : sp.status === 'current' ? 'active-tag' : 'upcoming';
    const tx = sp.status === 'completed' ? 'Done' : sp.status === 'current' ? 'Active' : 'Upcoming';
    const ic = sp.status === 'completed'
      ? '<polyline points="20 6 9 17 4 12"/>'
      : sp.status === 'current'
        ? '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'
        : '<circle cx="12" cy="12" r="10"/>';

    h += `<div class="tl-node ${c}" data-id="${sp.id}" onclick="selectSprint('${sp.id}')">
      <div class="tl-dot-wrap"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ic}</svg></div>
      <div class="tl-info">
        <div class="tl-sprint">${sp.name}</div>
        <div class="tl-dates">${fmtR(sp.dates[0], sp.dates[1])}</div>
        <div class="tl-status-tag ${t}">${tx}</div>
      </div>
    </div>`;
  });

  el.innerHTML = h;
}

// ── Sprint Selection ─────────────────────────────────────────
function selectSprint(id) {
  if (activeSprint === id) return;
  activeSprint = id;
  document.querySelectorAll('.tl-node').forEach(n => n.classList.remove('active'));
  document.querySelector(`.tl-node[data-id="${id}"]`)?.classList.add('active');

  const sp = SPRINTS.find(s => s.id === id);
  if (!sp) return;

  const p = document.getElementById('detailPanel');

  p.innerHTML = `
    <div class="detail-header">
      <div class="detail-icon"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
      <div>
        <div class="detail-title">${sp.name} — ONBOARD</div>
        <div class="detail-sub">${fmtR(sp.dates[0], sp.dates[1])}</div>
      </div>
    </div>

    <div class="tabs-strip">
      <div class="tab-item active" onclick="sTab('dp','summary',this)"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>AI Summary</div>
      <div class="tab-item" onclick="sTab('dp','meetings',this);loadSprintMeetings(${sp.sprint_number})"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>Meetings</div>
      <div class="tab-item" onclick="sTab('dp','outcomes',this);loadTickets()"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>Outcomes</div>
      <div class="tab-item" onclick="sTab('dp','decisions',this);loadDecisions()"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>Decisions</div>
    </div>

    <div class="tab-content active" id="dp-summary">
      <div class="ai-summary-box">
        <div class="ai-label"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 6v6l4 2"/><circle cx="18" cy="6" r="3" fill="currentColor" stroke="none"/></svg><span class="ai-dot"></span>AI Sprint Summary</div>
        <div class="ai-summary-text">${sp.aiSummary}</div>
      </div>
      ${sp.goal ? `<div class="sprint-goal-box">
        <div class="sprint-goal-label">Sprint Goal</div>
        <div class="sprint-goal-text">${esc(sp.goal)}</div>
      </div>` : ''}
    </div>

    <div class="tab-content" id="dp-meetings">
      <div class="decisions-loading"><div class="spinner"></div>Click Meetings tab to load…</div>
    </div>

    <div class="tab-content" id="dp-outcomes">
      <div class="decisions-loading"><div class="spinner"></div>Click to load outcomes…</div>
    </div>

    <div class="tab-content" id="dp-decisions">
      <div class="decisions-loading"><div class="spinner"></div>Click to load decisions...</div>
    </div>`;

  p.classList.remove('visible');
  p.offsetHeight;
  p.classList.add('visible');
  p.style.animation = 'none';
  p.offsetHeight;
  p.style.animation = '';

  // Auto-fetch ticket stats for this sprint
}

// ── Project Ticket Stats (overall) ───────────────────────────
let projectStatsLoaded = false;

function loadProjectTicketStats() {
  const el = document.getElementById('topbarStats');
  if (!el || projectStatsLoaded) return;

  el.innerHTML = '<span class="ts-loading">Loading stats…</span>';

  fetchTicketsOnce()
    .then(tickets => {
      projectStatsLoaded = true;
      renderProjectStats(el, tickets);
    })
    .catch(() => {
      el.innerHTML = '';
    });
}

function renderProjectStats(el, tickets) {
  const total = tickets.length;
  const completed = tickets.filter(t => t.is_completed).length;
  const pending = total - completed;

  // Count blockers (status = Blocked or priority = Critical/Highest)
  const blockers = tickets.filter(t => {
    const st = (t.status || '').toLowerCase();
    const pr = (t.priority || '').toLowerCase();
    return st === 'blocked' || pr === 'critical' || pr === 'highest';
  }).length;

  // Count in-progress
  const inProgress = tickets.filter(t => {
    const st = (t.status || '').toLowerCase();
    return st === 'in progress' || st === 'in_progress' || st === 'in review';
  }).length;

  // Total story points
  const totalPts = tickets.reduce((s, t) => s + (t.story_points || 0), 0);
  const completedPts = tickets.filter(t => t.is_completed).reduce((s, t) => s + (t.story_points || 0), 0);

  el.innerHTML = `
    <div class="ts-chip" style="--chip-c:var(--accent)"><span class="ts-num">${total}</span><span class="ts-txt">Tickets</span></div>
    <div class="ts-chip" style="--chip-c:var(--success)"><span class="ts-num">${completed}</span><span class="ts-txt">Done</span></div>
    <div class="ts-chip" style="--chip-c:var(--warn)"><span class="ts-num">${pending}</span><span class="ts-txt">Pending</span></div>
    ${blockers > 0 ? `<div class="ts-chip ts-blocker" style="--chip-c:var(--danger)"><span class="ts-num">${blockers}</span><span class="ts-txt">Blockers</span></div>` : ''}
    <div class="ts-chip" style="--chip-c:var(--accent2)"><span class="ts-num">${inProgress}</span><span class="ts-txt">In Progress</span></div>
    <div class="ts-chip" style="--chip-c:var(--text)"><span class="ts-num">${completedPts}/${totalPts}</span><span class="ts-txt">SP</span></div>
  `;
}

// ── Calendar Builder ─────────────────────────────────────────
function bCal(sp, meetings) {
  if (!meetings || !meetings.length) return '<p style="color:var(--muted);font-size:13px;padding:4px">No meetings scheduled for this sprint.</p>';

  // Parse sprint start/end as local dates (avoid UTC offset issues)
  const [sy, sm, sd] = sp.dates[0].split('-').map(Number);
  const [ey, em, ed] = sp.dates[1].split('-').map(Number);
  const stLocal = new Date(sy, sm - 1, sd);
  const enLocal = new Date(ey, em - 1, ed);

  // Build meeting map keyed by LOCAL date string (avoids UTC off-by-one)
  const mm = {};
  meetings.forEach(m => {
    const mDate = localDateStr(m.meeting_date || m.date || '');
    let type = 'planning';
    const titleLower = (m.title || '').toLowerCase();
    if (titleLower.includes('standup') || titleLower.includes('daily')) type = 'standup';
    else if (titleLower.includes('retro')) type = 'retro';
    else if (titleLower.includes('review') || titleLower.includes('demo') || titleLower.includes('mid-sprint') || titleLower.includes('midsprint')) type = 'review';
    mm[mDate] = { ...m, date: mDate, type, name: m.title || 'Meeting', project: 'ONBOARD', time: '' };
  });

  const td = new Date();
  const todayStr = `${td.getFullYear()}-${String(td.getMonth() + 1).padStart(2, '0')}-${String(td.getDate()).padStart(2, '0')}`;

  // Collect unique months that the sprint spans
  const months = [];
  let cur = new Date(sy, sm - 1, 1);
  const lastMonth = new Date(ey, em - 1, 1);
  while (cur <= lastMonth) {
    months.push({ yr: cur.getFullYear(), mo: cur.getMonth() });
    cur.setMonth(cur.getMonth() + 1);
  }

  let h = '';
  months.forEach(({ yr, mo }) => {
    const fd = new Date(yr, mo, 1).getDay();
    const dm = new Date(yr, mo + 1, 0).getDate();

    h += `<div class="cal-month"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>${MO[mo]} ${yr}</div><div class="cal-grid">`;

    ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(d => {
      h += `<div class="cal-head">${d}</div>`;
    });

    for (let i = 0; i < fd; i++) h += '<div class="cal-day"></div>';

    for (let d = 1; d <= dm; d++) {
      const ds = `${yr}-${String(mo + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const dO = new Date(yr, mo, d);
      const iS = dO >= stLocal && dO <= enLocal;
      const iT = ds === todayStr;
      const m = mm[ds];
      let c = 'cal-day';
      if (iS) c += ' in-sprint';
      if (iT) c += ' today';
      if (m) c += ` has-meeting type-${m.type}`;

      // Hover tooltip for meeting dates
      const titleAttr = m ? ` title="${esc(m.name)}"` : '';
      const clickAttr = m ? ` onclick="window.openMeetingPopup('${m.date}','${esc(m.type)}','${esc(m.name)}','${esc(m.project)}','${esc(m.time)}','${esc((m.summary || '').replace(/'/g, "&#39;"))}')"` : '';

      h += `<div class="${c}"${titleAttr}${clickAttr}>${d}</div>`;
    }

    h += '</div>';
  });

  h += '<div class="cal-legend"><div class="cal-legend-item"><div class="cal-legend-dot" style="background:var(--accent)"></div>Planning</div><div class="cal-legend-item"><div class="cal-legend-dot" style="background:var(--success)"></div>Standup</div><div class="cal-legend-item"><div class="cal-legend-dot" style="background:var(--accent2)"></div>Review</div><div class="cal-legend-item"><div class="cal-legend-dot" style="background:var(--warn)"></div>Retro</div></div>';
  return h;
}

// ── Load Sprint Meetings from API ────────────────────────────
let sprintMeetingsCache = {};

function loadSprintMeetings(sprintNumber) {
  const container = document.getElementById('dp-meetings');
  if (!container) return;

  // Check cache first
  if (sprintMeetingsCache[sprintNumber]) {
    const sp = SPRINTS.find(s => s.sprint_number === sprintNumber);
    if (sp) container.innerHTML = bCal(sp, sprintMeetingsCache[sprintNumber]);
    return;
  }

  container.innerHTML = '<div class="decisions-loading"><div class="spinner"></div>Fetching sprint meetings…</div>';

  fetch(`/api/sprints/${sprintNumber}/meetings/`)
    .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then(data => {
      const meetings = Array.isArray(data) ? data : (data.results || []);
      sprintMeetingsCache[sprintNumber] = meetings;
      const sp = SPRINTS.find(s => s.sprint_number === sprintNumber);
      if (sp && container) {
        container.innerHTML = bCal(sp, meetings);
      }
    })
    .catch(err => {
      container.innerHTML = `<div class="decisions-error">⚠ Failed to load meetings: ${err.message}<br><button class="btn btn-ghost" style="margin-top:12px" onclick="window.loadSprintMeetings(${sprintNumber})">Retry</button></div>`;
    });
}

// ── Tab Switching ────────────────────────────────────────────
function sTab(px, tab, btn) {
  const p = document.getElementById('detailPanel');
  p.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
  p.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(`${px}-${tab}`)?.classList.add('active');
}

// ── Outcome Item Builder ─────────────────────────────────────
function oIt(i) {
  const t = i.status === 'Blocked' ? 'blocker' : i.status === 'Done' ? 'action' : 'build';
  const bt = i.status === 'Blocked' ? 'Blocker' : i.status === 'Done' ? 'Completed' : i.status === 'To Do' ? 'To Do' : 'In Progress';
  const bc = i.status === 'Blocked' ? 'blocker' : 'action';
  const ic = t === 'blocker'
    ? '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
    : t === 'action'
      ? '<polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'
      : '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>';

  return `<div class="outcome-item"><div class="outcome-icon-wrap ${t}"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ic}</svg></div><div><div class="outcome-text"><strong>${i.assignee}</strong> — ${i.summary}<span class="outcome-badge ${bc}">${bt}</span></div><div class="outcome-owner">${i.issue_key} · ${i.story_points} pts · ${i.priority}</div></div></div>`;
}

// ── Decisions API Integration ────────────────────────────────

// Cache for source detail lookups (meeting / confluence)
const _srcCache = {};

// Enrich decisions with source detail (meeting title/date, confluence title/space)
async function enrichDecisionSources(decisions) {
  const fetches = decisions.map(async d => {
    const src = (d.source_type || '').toLowerCase();
    const sid = d.source_id;
    if (!sid) return;

    const cacheKey = `${src}:${sid}`;
    if (_srcCache[cacheKey]) { d._sourceDetail = _srcCache[cacheKey]; return; }

    let url = null;
    if (src === 'meeting')    url = `/api/meetings/${encodeURIComponent(sid)}/`;
    if (src === 'confluence')  url = `/api/pages/${encodeURIComponent(sid)}/`;
    if (!url) return;

    try {
      const r = await fetch(url);
      if (!r.ok) return;
      const json = await r.json();
      _srcCache[cacheKey] = json;
      d._sourceDetail = json;
    } catch (_) { /* silently skip — card will fall back to raw source_id */ }
  });
  await Promise.all(fetches);
}

function loadDecisions() {
  const container = document.getElementById('dp-decisions');
  if (!container) return;

  if (decisionsLoaded) {
    renderDecisions(container, decisionsData);
    return;
  }

  container.innerHTML = '<div class="decisions-loading"><div class="spinner"></div>Fetching decisions from API...</div>';

  fetch('/api/decisions/')
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(async data => {
      decisionsData = Array.isArray(data) ? data : (data.results || []);
      container.innerHTML = '<div class="decisions-loading"><div class="spinner"></div>Enriching source details...</div>';
      await enrichDecisionSources(decisionsData);
      decisionsLoaded = true;
      renderDecisions(container, decisionsData);
    })
    .catch(err => {
      container.innerHTML = `<div class="decisions-error">⚠ Failed to load decisions: ${err.message}<br><button class="btn btn-ghost" style="margin-top:12px" onclick="window.decisionsLoaded=false;window.loadDecisions()">Retry</button></div>`;
    });
}

// Category icon map — SVG paths for known categories
const CAT_ICONS = {
  architecture: '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>',
  process:      '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
  security:     '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
  technology:   '<rect x="4" y="4" width="16" height="16" rx="2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/>',
  data:         '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
  design:       '<path d="M12 19l7-7 3 3-7 7-3-3z"/><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="M2 2l7.586 7.586"/><circle cx="11" cy="11" r="2"/>',
  _default:     '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'
};

function getCatIcon(category) {
  const key = (category || '').toLowerCase();
  for (const k of Object.keys(CAT_ICONS)) {
    if (k !== '_default' && key.includes(k)) return CAT_ICONS[k];
  }
  return CAT_ICONS._default;
}

// ── Current decisions view state ──
let dtlViewMode = 'overall';   // 'overall' | 'grouped' | 'filter'
let dtlActiveFilter = null;    // selected category in filter mode

// ── Source detail block builder ──
function buildSourceBlock(d) {
  const src = (d.source_type || '').toLowerCase();
  const det = d._sourceDetail;
  if (!det) return '';

  if (src === 'meeting') {
    const mDate = det.meeting_date ? new Date(det.meeting_date) : null;
    const dateStr = mDate ? `${MO[mDate.getMonth()]} ${mDate.getDate()}, ${mDate.getFullYear()}` : '';
    return `<div class="dtl-source-block dtl-source-meeting">
      <div class="dtl-source-icon"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div>
      <div class="dtl-source-info">
        <div class="dtl-source-label">Meeting</div>
        <div class="dtl-source-title">${esc(det.title)}</div>
        ${dateStr ? `<div class="dtl-source-sub"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;stroke:var(--muted);fill:none;vertical-align:-1px;margin-right:4px"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>${dateStr}</div>` : ''}
      </div>
    </div>`;
  }

  if (src === 'confluence') {
    return `<div class="dtl-source-block dtl-source-confluence">
      <div class="dtl-source-icon"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg></div>
      <div class="dtl-source-info">
        <div class="dtl-source-label">Confluence</div>
        <div class="dtl-source-title">${esc(det.title)}</div>
        ${det.space ? `<div class="dtl-source-sub"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;stroke:var(--muted);fill:none;vertical-align:-1px;margin-right:4px"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>${esc(det.space)}</div>` : ''}
      </div>
    </div>`;
  }

  return '';
}

// ── Shared: render a single decision entry card ──
function renderDecisionEntry(d, showCatBadge) {
  const confPct = Math.min(Math.max((d.confidence_score || 0), 0), 1) * 100;
  const confColor = confPct >= 70 ? 'var(--success)' : confPct >= 40 ? 'var(--warn)' : 'var(--danger)';
  const statusCls = d.status === 'active' ? 'active' : d.status === 'superseded' ? 'superseded' : d.status === 'deprecated' ? 'deprecated' : 'draft';
  const cat = d.category || 'Uncategorized';

  return `<div class="dtl-entry status-${statusCls}">
    <div class="dtl-node"><div class="dtl-node-dot"></div></div>
    <div class="dtl-date">${d.decision_date || 'No date'}</div>
    <div class="dtl-card">
      <div class="dtl-card-top">
        <div class="dtl-title">${esc(d.title || 'Untitled')}</div>
        <div class="dtl-card-badges">
          ${showCatBadge ? `<span class="dtl-cat-badge">${esc(cat)}</span>` : ''}
          <span class="decision-status ${statusCls}">${esc(d.status || 'unknown')}</span>
        </div>
      </div>
      <div class="dtl-desc">${esc(d.description || '')}</div>
      ${d.rationale ? `<div class="dtl-rationale"><strong style="color:var(--accent);font-size:10px;text-transform:uppercase;letter-spacing:.5px">Rationale</strong><br>${esc(d.rationale)}</div>` : ''}
      ${d._sourceDetail ? buildSourceBlock(d) : ''}
      <div class="dtl-meta-row">
        <div class="dtl-meta-item">
          <div class="dtl-meta-label">Source</div>
          <div class="dtl-meta-val">${esc(d.source_type || '—')}</div>
        </div>
        <div class="dtl-meta-item">
          <div class="dtl-meta-label">Source ID</div>
          <div class="decision-uuid">${esc(d.source_id || '—')}</div>
        </div>
        <div class="dtl-meta-item">
          <div class="dtl-meta-label">Confidence</div>
          <div class="decision-confidence">
            <div class="confidence-bar"><div class="confidence-fill" style="width:${confPct}%;background:${confColor}"></div></div>
            <span style="font-family:var(--font-mono);font-size:11px;color:${confColor}">${(d.confidence_score || 0).toFixed(2)}</span>
          </div>
        </div>
        ${d.superseded_by ? `<div class="dtl-meta-item"><div class="dtl-meta-label">Superseded By</div><div class="decision-uuid">${esc(d.superseded_by)}</div></div>` : ''}
        ${d.supersedes ? `<div class="dtl-meta-item"><div class="dtl-meta-label">Supersedes</div><div class="decision-uuid">${esc(d.supersedes)}</div></div>` : ''}
      </div>
      ${d.decided_by && d.decided_by.length ? `<div style="margin-bottom:8px"><div class="dtl-meta-label" style="margin-bottom:5px">Decided By</div><div class="decision-decided-by">${d.decided_by.map(p => `<span class="decided-by-chip">${esc(p)}</span>`).join('')}</div></div>` : ''}
      ${d.related_decisions && d.related_decisions.length ? `<div style="margin-bottom:8px"><div class="dtl-meta-label" style="margin-bottom:5px">Related Decisions</div>${d.related_decisions.map(rd => `<div class="decision-uuid" style="margin-bottom:2px">${esc(rd)}</div>`).join('')}</div>` : ''}
      ${d.tags && d.tags.length ? `<div class="decision-tags">${d.tags.map(t => `<span class="decision-tag">${esc(t)}</span>`).join('')}</div>` : ''}
    </div>
  </div>`;
}

// ── View 1: Overall flat timeline ──
function renderOverall(decisions) {
  const sorted = [...decisions].sort((a, b) => (b.decision_date || '').localeCompare(a.decision_date || ''));
  return `<div class="decisions-timeline">${sorted.map(d => renderDecisionEntry(d, true)).join('')}</div>`;
}

// ── View 2: Grouped by category ──
function renderGrouped(decisions) {
  const groups = {};
  decisions.forEach(d => {
    const cat = d.category || 'Uncategorized';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(d);
  });
  const catOrder = Object.keys(groups).sort((a, b) => {
    if (a === 'Uncategorized') return 1;
    if (b === 'Uncategorized') return -1;
    return a.localeCompare(b);
  });
  let h = '';
  catOrder.forEach(cat => {
    const items = groups[cat].sort((a, b) => (b.decision_date || '').localeCompare(a.decision_date || ''));
    const activeCount = items.filter(d => d.status === 'active').length;
    const iconSvg = getCatIcon(cat);
    h += `<div class="dtl-category-section">
      <div class="dtl-category-header">
        <div class="dtl-category-icon"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${iconSvg}</svg></div>
        <div class="dtl-category-info">
          <div class="dtl-category-name">${esc(cat)}</div>
          <div class="dtl-category-count">${items.length} decision${items.length !== 1 ? 's' : ''}${activeCount ? ' · ' + activeCount + ' active' : ''}</div>
        </div>
      </div>
      <div class="decisions-timeline">${items.map(d => renderDecisionEntry(d, false)).join('')}</div>
    </div>`;
  });
  return h;
}

// ── View 3: Category filter ──
function renderFilter(decisions, activeCat) {
  // Collect unique categories
  const cats = [...new Set(decisions.map(d => d.category || 'Uncategorized'))].sort((a, b) => {
    if (a === 'Uncategorized') return 1;
    if (b === 'Uncategorized') return -1;
    return a.localeCompare(b);
  });

  // Build filter chips bar
  let h = `<div class="dtl-filter-bar">`;
  cats.forEach(cat => {
    const count = decisions.filter(d => (d.category || 'Uncategorized') === cat).length;
    const sel = activeCat === cat ? ' active' : '';
    const iconSvg = getCatIcon(cat);
    h += `<button class="dtl-filter-chip${sel}" onclick="window.setDtlFilter('${esc(cat).replace(/'/g, "\\'")}')"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${iconSvg}</svg>${esc(cat)}<span class="dtl-filter-count">${count}</span></button>`;
  });
  h += `</div>`;

  // Show timeline for selected category (or prompt)
  if (activeCat) {
    const filtered = decisions
      .filter(d => (d.category || 'Uncategorized') === activeCat)
      .sort((a, b) => (b.decision_date || '').localeCompare(a.decision_date || ''));
    h += `<div class="decisions-timeline">${filtered.map(d => renderDecisionEntry(d, false)).join('')}</div>`;
  } else {
    h += `<div class="decisions-empty" style="margin-top:8px">Select a category above to filter decisions.</div>`;
  }
  return h;
}

// ── Main render controller ──
function renderDecisions(container, decisions) {
  if (!decisions.length) {
    container.innerHTML = '<div class="decisions-empty">No decisions found.</div>';
    return;
  }

  // Toolbar
  const totalCount = decisions.length;
  const catCount = new Set(decisions.map(d => d.category || 'Uncategorized')).size;
  const toolbar = `<div class="dtl-toolbar">
    <div class="dtl-toolbar-left">
      <button class="dtl-view-btn${dtlViewMode === 'overall' ? ' active' : ''}" onclick="window.setDtlView('overall')">
        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="17" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="17" y1="18" x2="3" y2="18"/></svg>
        Overall
      </button>
      <button class="dtl-view-btn${dtlViewMode === 'grouped' ? ' active' : ''}" onclick="window.setDtlView('grouped')">
        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
        Grouped
      </button>
      <button class="dtl-view-btn${dtlViewMode === 'filter' ? ' active' : ''}" onclick="window.setDtlView('filter')">
        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
        Filter
      </button>
    </div>
    <div class="dtl-toolbar-right">
      <span class="dtl-toolbar-stat">${totalCount} decisions</span>
      <span class="dtl-toolbar-stat">${catCount} categories</span>
    </div>
  </div>`;

  // Body based on current view mode
  let body = '';
  if (dtlViewMode === 'overall')      body = renderOverall(decisions);
  else if (dtlViewMode === 'grouped') body = renderGrouped(decisions);
  else if (dtlViewMode === 'filter')  body = renderFilter(decisions, dtlActiveFilter);

  container.innerHTML = toolbar + `<div class="dtl-view-body">${body}</div>`;
}

// ── View switchers (exposed globally) ──
function setDtlView(mode) {
  dtlViewMode = mode;
  dtlActiveFilter = null;
  const container = document.getElementById('dp-decisions');
  if (container && decisionsData.length) renderDecisions(container, decisionsData);
}
function setDtlFilter(cat) {
  dtlActiveFilter = dtlActiveFilter === cat ? null : cat; // toggle
  const container = document.getElementById('dp-decisions');
  if (container && decisionsData.length) renderDecisions(container, decisionsData);
}

// ── Tickets / Outcomes API Integration ───────────────────────
let ticketsLoaded = false;
let ticketsData = [];
let tktViewMode = 'all';       // 'all' | 'sprint' | 'assignee'
let tktActiveFilter = null;

const ISSUE_ICONS = {
  Epic:  '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
  Story: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  Task:  '<polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
  Bug:   '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'
};

function loadTickets() {
  const container = document.getElementById('dp-outcomes');
  if (!container) return;
  if (ticketsLoaded) { renderTickets(container, ticketsData); return; }
  container.innerHTML = '<div class="decisions-loading"><div class="spinner"></div>Fetching outcomes from API…</div>';
  fetchTicketsOnce()
    .then(data => {
      ticketsLoaded = true;
      ticketsData = data;
      renderTickets(container, ticketsData);
    })
    .catch(err => {
      _ticketsCachePromise = null; // allow retry
      container.innerHTML = `<div class="decisions-error">⚠ Failed to load outcomes: ${err.message}<br><button class="btn btn-ghost" style="margin-top:12px" onclick="window.ticketsLoaded=false;window.loadTickets()">Retry</button></div>`;
    });
}

// ── Shared ticket card renderer ──
function renderTicketEntry(t) {
  const icon = ISSUE_ICONS[t.issue_type] || ISSUE_ICONS.Task;
  const pc = t.priority === 'Critical' ? 'var(--danger)' : t.priority === 'High' ? 'var(--warn)' : t.priority === 'Medium' ? 'var(--accent)' : 'var(--muted)';
  const rd = t.resolved_date ? new Date(t.resolved_date) : null;
  const resolvedStr = rd ? `${MO[rd.getMonth()]} ${rd.getDate()}, ${rd.getFullYear()}` : '—';
  const comments = (t.comments || '').split('\n').filter(c => c.trim());

  return `<div class="tkt-card">
    <div class="tkt-header">
      <div class="tkt-issue-info">
        <div class="tkt-type-icon"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${icon}</svg></div>
        <span class="tkt-issue-key">${esc(t.issue_key)}</span>
        <span class="tkt-type-label">${esc(t.issue_type)}</span>
      </div>
      <div class="tkt-header-badges">
        ${t.story_points ? `<span class="tkt-pts">${t.story_points} pts</span>` : ''}
        <span class="tkt-priority" style="color:${pc};border-color:${pc}">${esc(t.priority)}</span>
      </div>
    </div>
    <div class="tkt-summary">${esc(t.summary)}</div>
    ${t.description ? `<div class="tkt-desc">${esc(t.description)}</div>` : ''}
    <div class="tkt-meta">
      <div class="tkt-meta-item"><div class="tkt-meta-label">Assignee</div><div class="tkt-meta-val"><span class="tkt-avatar" style="background:${gr(t.assignee || 'U')}">${ini(t.assignee || 'U')}</span>${esc(t.assignee || 'Unassigned')}</div></div>
      <div class="tkt-meta-item"><div class="tkt-meta-label">Reporter</div><div class="tkt-meta-val">${esc(t.reporter || '—')}</div></div>
      <div class="tkt-meta-item"><div class="tkt-meta-label">Resolved</div><div class="tkt-meta-val" style="font-family:var(--font-mono);font-size:11px">${resolvedStr}</div></div>
      ${t.sprint ? `<div class="tkt-meta-item"><div class="tkt-meta-label">Sprint</div><div class="tkt-meta-val">${esc(t.sprint)}</div></div>` : ''}
    </div>
    ${t.labels && t.labels.length ? `<div class="tkt-labels">${t.labels.map(l => `<span class="tkt-label">${esc(l)}</span>`).join('')}</div>` : ''}
    ${comments.length ? `<div class="tkt-comments"><div class="tkt-comments-header"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>${comments.length} comment${comments.length !== 1 ? 's' : ''}</div><div class="tkt-comments-list">${comments.map(c => `<div class="tkt-comment">${esc(c)}</div>`).join('')}</div></div>` : ''}
  </div>`;
}

// ── View 1: All completed tickets ──
function renderTicketsAll(tickets) {
  const sorted = [...tickets].sort((a, b) => (b.resolved_date || '').localeCompare(a.resolved_date || ''));
  return `<div class="tkt-list">${sorted.map(t => renderTicketEntry(t)).join('')}</div>`;
}

// ── View 2: Grouped by sprint ──
function renderTicketsBySprint(tickets) {
  const groups = {};
  tickets.forEach(t => { const sp = t.sprint || 'Unassigned'; if (!groups[sp]) groups[sp] = []; groups[sp].push(t); });
  const order = Object.keys(groups).sort((a, b) => {
    if (a === 'Unassigned') return 1; if (b === 'Unassigned') return -1;
    return a.localeCompare(b);
  });
  let h = '';
  order.forEach(sp => {
    const items = groups[sp].sort((a, b) => (b.resolved_date || '').localeCompare(a.resolved_date || ''));
    const pts = items.reduce((s, t) => s + (t.story_points || 0), 0);
    h += `<div class="tkt-sprint-section">
      <div class="tkt-sprint-header">
        <div class="tkt-sprint-icon"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div>
        <div class="tkt-sprint-info"><div class="tkt-sprint-name">${esc(sp)}</div><div class="tkt-sprint-stats">${items.length} completed · ${pts} pts</div></div>
      </div>
      <div class="tkt-list">${items.map(t => renderTicketEntry(t)).join('')}</div>
    </div>`;
  });
  return h;
}

// ── View 3: Filter by assignee ──
function renderTicketsByAssignee(tickets, active) {
  const names = [...new Set(tickets.map(t => t.assignee || 'Unassigned'))].sort();
  let h = `<div class="dtl-filter-bar">`;
  names.forEach(name => {
    const count = tickets.filter(t => (t.assignee || 'Unassigned') === name).length;
    const sel = active === name ? ' active' : '';
    h += `<button class="dtl-filter-chip${sel}" onclick="window.setTktFilter('${esc(name).replace(/'/g, "\\'")}')"><span class="tkt-avatar-sm" style="background:${gr(name)}">${ini(name)}</span>${esc(name)}<span class="dtl-filter-count">${count}</span></button>`;
  });
  h += `</div>`;
  if (active) {
    const filtered = tickets.filter(t => (t.assignee || 'Unassigned') === active).sort((a, b) => (b.resolved_date || '').localeCompare(a.resolved_date || ''));
    h += `<div class="tkt-list">${filtered.map(t => renderTicketEntry(t)).join('')}</div>`;
  } else {
    h += `<div class="decisions-empty" style="margin-top:8px">Select a team member above to filter outcomes.</div>`;
  }
  return h;
}

// ── Main tickets render controller ──
function renderTickets(container, tickets) {
  const completed = tickets.filter(t => t.status === 'Done' && t.is_completed === true);
  if (!completed.length) { container.innerHTML = '<div class="decisions-empty">No completed outcomes found.</div>'; return; }

  const totalPts = completed.reduce((s, t) => s + (t.story_points || 0), 0);
  const memberCount = new Set(completed.map(t => t.assignee)).size;

  const toolbar = `<div class="dtl-toolbar">
    <div class="dtl-toolbar-left">
      <button class="dtl-view-btn${tktViewMode === 'all' ? ' active' : ''}" onclick="window.setTktView('all')">
        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="17" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="17" y1="18" x2="3" y2="18"/></svg>
        All
      </button>
      <button class="dtl-view-btn${tktViewMode === 'sprint' ? ' active' : ''}" onclick="window.setTktView('sprint')">
        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        By Sprint
      </button>
      <button class="dtl-view-btn${tktViewMode === 'assignee' ? ' active' : ''}" onclick="window.setTktView('assignee')">
        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        By Assignee
      </button>
    </div>
    <div class="dtl-toolbar-right">
      <span class="dtl-toolbar-stat">${completed.length} completed</span>
      <span class="dtl-toolbar-stat">${totalPts} pts</span>
      <span class="dtl-toolbar-stat">${memberCount} members</span>
    </div>
  </div>`;

  let body = '';
  if (tktViewMode === 'all')           body = renderTicketsAll(completed);
  else if (tktViewMode === 'sprint')   body = renderTicketsBySprint(completed);
  else if (tktViewMode === 'assignee') body = renderTicketsByAssignee(completed, tktActiveFilter);

  container.innerHTML = toolbar + `<div class="dtl-view-body">${body}</div>`;
}

function setTktView(mode) {
  tktViewMode = mode;
  tktActiveFilter = null;
  const container = document.getElementById('dp-outcomes');
  if (container && ticketsData.length) renderTickets(container, ticketsData);
}
function setTktFilter(name) {
  tktActiveFilter = tktActiveFilter === name ? null : name;
  const container = document.getElementById('dp-outcomes');
  if (container && ticketsData.length) renderTickets(container, ticketsData);
}

// ── Meeting Popup ────────────────────────────────────────────

function getMeetingTypeColor(type) {
  switch (type) {
    case 'standup': return 'var(--success)';
    case 'retro':   return 'var(--warn)';
    case 'review':  return 'var(--accent2)';
    default:        return 'var(--accent)';
  }
}

function getMeetingTypeIcon(type) {
  switch (type) {
    case 'standup':  return '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>';
    case 'retro':    return '<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>';
    case 'review':   return '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
    case 'planning': return '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>';
    default:         return '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>';
  }
}

function splitItems(val) {
  if (!val) return [];
  // API returns arrays; local data may be a string
  if (Array.isArray(val)) return val.map(s => String(s).trim()).filter(Boolean);
  return String(val).split(/\n|(?:\d+\.\s)|\s*[;•–—]\s*/)
    .map(s => s.trim())
    .filter(s => s.length > 0);
}

function renderParticipants(participantsVal) {
  if (!participantsVal) return '<span class="mp-empty">No participants listed</span>';
  // API returns array; local data may be comma-separated string
  let names;
  if (Array.isArray(participantsVal)) {
    names = participantsVal.map(s => String(s).trim()).filter(Boolean);
  } else {
    names = String(participantsVal).split(/[,;\n]+/).map(s => s.trim()).filter(Boolean);
  }
  if (!names.length) return '<span class="mp-empty">No participants listed</span>';
  return `<div class="mp-participants-wrap">${names.map(n => {
    const initials = n.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
    return `<div class="mp-participant"><div class="mp-participant-avatar" style="background:${gr(n)}">${initials}</div><div class="mp-participant-name">${esc(n)}</div></div>`;
  }).join('')}</div>`;
}

function openMeetingPopup(date, type, name, project, time, fallbackSummary) {
  const overlay = document.getElementById('meetingPopupOverlay');
  const popup = document.getElementById('meetingPopup');
  const tc = getMeetingTypeColor(type);
  const typeIcon = getMeetingTypeIcon(type);

  // Show loading state immediately
  popup.innerHTML = `
    <div class="mp-header">
      <div class="mp-type-icon" style="background:${tc}"><svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">${typeIcon}</svg></div>
      <div class="mp-header-info">
        <div class="mp-type-badge" style="color:${tc}"><div class="mp-type-dot" style="background:${tc}"></div>${type.charAt(0).toUpperCase() + type.slice(1)}</div>
        <div class="mp-title">${esc(name)}</div>
        <div class="mp-date">${esc(date)} · ${esc(project)} · ${esc(time)}</div>
      </div>
      <button class="mp-close" onclick="closeMeetingPopup()"><svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
    <div class="mp-body">
      <div class="mp-loading"><div class="spinner"></div>Fetching meeting details...</div>
    </div>`;
  overlay.classList.add('visible');

  // Try fetching from API
  fetch('/api/meetings/')
    .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then(data => {
      const meetings = Array.isArray(data) ? data : (data.results || []);

      // 1. Try exact date match first (compare local dates)
      let match = meetings.find(m => {
        const mDate = localDateStr(m.meeting_date || '');
        return mDate === date;
      });

      // 2. Fallback: match by meeting type keyword in title
      if (!match) {
        const typeKeywords = {
          planning: ['planning'],
          standup:  ['standup', 'daily'],
          review:  ['review', 'midsprint', 'mid-sprint', 'demo'],
          retro:   ['retro', 'retrospective'],
        };
        const keywords = typeKeywords[type] || [type];
        match = meetings.find(m => {
          const t = (m.title || '').toLowerCase();
          return keywords.some(k => t.includes(k));
        });
      }

      // 3. Fallback: just use the first meeting if any exist
      if (!match && meetings.length) {
        match = meetings[0];
      }

      if (match) {
        renderMeetingPopupContent(match, type, tc, typeIcon);
      } else {
        renderMeetingPopupFallback(date, type, name, project, time, fallbackSummary, tc, typeIcon);
      }
    })
    .catch(() => {
      // API unavailable — use local data
      renderMeetingPopupFallback(date, type, name, project, time, fallbackSummary, tc, typeIcon);
    });
}

function renderMeetingPopupContent(m, type, tc, typeIcon) {
  const popup = document.getElementById('meetingPopup');
  const title = m.title || 'Untitled Meeting';
  // Use localDate to avoid UTC→local timezone shift on date display
  const mDateObj = m.meeting_date ? localDate(m.meeting_date) : null;
  const mDate = mDateObj ? mDateObj.toLocaleString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'No date';
  const duration = m.duration_seconds ? `${Math.round(m.duration_seconds / 60)} min` : '';

  const decisions = splitItems(m.key_decisions);
  const actions = splitItems(m.action_items);

  popup.innerHTML = `
    <div class="mp-header">
      <div class="mp-type-icon" style="background:${tc}"><svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">${typeIcon}</svg></div>
      <div class="mp-header-info">
        <div class="mp-type-badge" style="color:${tc}"><div class="mp-type-dot" style="background:${tc}"></div>${type.charAt(0).toUpperCase() + type.slice(1)}</div>
        <div class="mp-title">${esc(title)}</div>
        <div class="mp-date">${mDate}${duration ? ' · Duration: ' + duration : ''}</div>
      </div>
      <button class="mp-close" onclick="closeMeetingPopup()"><svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
    <div class="mp-body">
      ${m.summary ? `
      <div class="mp-section">
        <div class="mp-section-label"><svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><line x1="17" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="17" y1="18" x2="3" y2="18"/></svg>Summary</div>
        <div class="mp-summary-text">${esc(m.summary)}</div>
      </div>` : ''}
      ${decisions.length ? `
      <div class="mp-section">
        <div class="mp-section-label"><svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>Key Decisions</div>
        <div class="mp-decisions-list">${decisions.map((d, i) => `
          <div class="mp-decision-item">
            <div class="mp-decision-num">${i + 1}.</div>
            <div>${esc(d)}</div>
          </div>`).join('')}
        </div>
      </div>` : ''}
      ${actions.length ? `
      <div class="mp-section">
        <div class="mp-section-label"><svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>Action Items</div>
        <div class="mp-actions-list">${actions.map((a, i) => `
          <div class="mp-action-item">
            <div class="mp-action-num">${i + 1}.</div>
            <div>${esc(a)}</div>
          </div>`).join('')}
        </div>
      </div>` : ''}
      <div class="mp-section">
        <div class="mp-section-label"><svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>Participants</div>
        ${renderParticipants(m.participants)}
      </div>
    </div>`;
}

function renderMeetingPopupFallback(date, type, name, project, time, summary, tc, typeIcon) {
  const popup = document.getElementById('meetingPopup');
  popup.innerHTML = `
    <div class="mp-header">
      <div class="mp-type-icon" style="background:${tc}"><svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">${typeIcon}</svg></div>
      <div class="mp-header-info">
        <div class="mp-type-badge" style="color:${tc}"><div class="mp-type-dot" style="background:${tc}"></div>${type.charAt(0).toUpperCase() + type.slice(1)}</div>
        <div class="mp-title">${esc(name)}</div>
        <div class="mp-date">${esc(date)} · ${esc(project)} · ${esc(time)}</div>
      </div>
      <button class="mp-close" onclick="closeMeetingPopup()"><svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
    <div class="mp-body">
      <div class="mp-section">
        <div class="mp-section-label"><svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><line x1="17" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="17" y1="18" x2="3" y2="18"/></svg>Summary</div>
        <div class="mp-summary-text">${esc(summary)}</div>
      </div>
      <div class="mp-section">
        <div class="mp-section-label" style="color:var(--muted);font-style:italic"><svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>Detailed data (decisions, participants) will appear when the API is available</div>
      </div>
    </div>`;
}

function closeMeetingPopup() {
  document.getElementById('meetingPopupOverlay').classList.remove('visible');
}

// Close on Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeMeetingPopup();
});

// Close on clicking overlay background
document.getElementById('meetingPopupOverlay')?.addEventListener('click', e => {
  if (e.target === e.currentTarget) closeMeetingPopup();
});

// ── Sidebar: Project Icon Rail + Flyout ──────────────────────
const PRJ_GRADIENTS = [
  'linear-gradient(135deg,#1e8fff,#6c5ce7)',
  'linear-gradient(135deg,#00d48a,#0abde3)',
  'linear-gradient(135deg,#f5a623,#ff6b6b)',
  'linear-gradient(135deg,#e84393,#fd79a8)',
  'linear-gradient(135deg,#6c5ce7,#a29bfe)',
  'linear-gradient(135deg,#0abde3,#1e8fff)',
];
let projectsCache = [];

async function loadProjectRail() {
  const rail = document.getElementById('projectRail');
  if (!rail) return;
  try {
    const res = await fetch('/api/projects/');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    projectsCache = Array.isArray(data) ? data : (data.results || []);
    if (!projectsCache.length) {
      rail.innerHTML = '<span style="font-size:11px;color:var(--muted);padding:2px 0">No projects</span>';
      return;
    }
    const currentPid = new URLSearchParams(window.location.search).get('project');
    const currentPage = new URLSearchParams(window.location.search).get('page') || 'overview';
    rail.innerHTML = projectsCache.map((p, i) => {
      const initials = (p.name || '').split(/\s+/).map(w => w[0]).join('').substring(0, 2).toUpperCase();
      const bg = PRJ_GRADIENTS[i % PRJ_GRADIENTS.length];
      const isActive = p.id === currentPid;
      const statusCls = (p.status || 'active').toLowerCase().replace(/\s+/g, '_');
      const overviewUrl = `project_dashboard.html?project=${p.id}&page=overview`;
      const integrationsUrl = `project_dashboard.html?project=${p.id}&page=integrations`;
      return `<div class="prj-item${isActive ? ' active-prj' : ''}" data-label="${esc(p.name)}" data-idx="${i}" onclick="navigateToPage('${p.id}','overview')" onmouseenter="showProjectFlyout(event,${i})" onmouseleave="hideProjectFlyout()">`
        + `<span class="prj-name">${esc(p.name)}</span>`
        + `<span class="prj-status-dot s-${statusCls}"></span></div>`
        + `<div class="prj-sub-links${isActive ? ' expanded' : ''}">`
        + `<a class="prj-sub-link${isActive && currentPage === 'overview' ? ' active-sub' : ''}" href="javascript:void(0)" onclick="navigateToPage('${p.id}','overview')"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg><span class="nav-label">Overview</span></a>`
        + `<a class="prj-sub-link${isActive && currentPage === 'integrations' ? ' active-sub' : ''}" href="javascript:void(0)" onclick="navigateToPage('${p.id}','integrations')"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg><span class="nav-label">Integrations</span></a>`
        + `</div>`;
    }).join('');
    // Update page title with the active project name
    updatePageTitle(currentPid);
  } catch (e) {
    console.error('Failed to load project rail:', e);
    rail.innerHTML = '<span style="font-size:11px;color:var(--muted)">—</span>';
  }
}

let flyoutTimer = null;
function showProjectFlyout(e, idx) {
  clearTimeout(flyoutTimer);
  const p = projectsCache[idx];
  if (!p) return;
  const flyout = document.getElementById('projectFlyout');
  const orb = e.currentTarget;
  const rect = orb.getBoundingClientRect();

  // Position flyout to the right of the item
  const sidebarEl = document.getElementById('sidebar');
  const sidebarRect = sidebarEl ? sidebarEl.getBoundingClientRect() : { right: rect.right + 12 };
  flyout.style.left = (sidebarRect.right + 8) + 'px';
  flyout.style.top  = (rect.top - 4) + 'px';

  // Populate content
  document.getElementById('flyoutTitle').textContent = p.name;
  const statusCls = (p.status || 'active').toLowerCase().replace(/\s+/g, '_');
  const statusEl = document.getElementById('flyoutStatus');
  statusEl.textContent = (p.status || 'active').replace(/_/g, ' ');
  statusEl.className = 'flyout-status s-' + statusCls;

  const body = document.getElementById('flyoutBody');
  body.textContent = p.description || 'No description available.';

  const link = document.getElementById('flyoutLink');
  link.href = 'javascript:void(0)';
  link.onclick = () => { hideProjectFlyout(); navigateToPage(p.id, 'overview'); };

  flyout.classList.add('visible');
}

function hideProjectFlyout() {
  flyoutTimer = setTimeout(() => {
    document.getElementById('projectFlyout')?.classList.remove('visible');
  }, 200);
}

// Keep flyout open while hovering over it
setTimeout(() => {
  const flyout = document.getElementById('projectFlyout');
  if (flyout) {
    flyout.addEventListener('mouseenter', () => clearTimeout(flyoutTimer));
    flyout.addEventListener('mouseleave', () => hideProjectFlyout());
  }
}, 0);

// ── Project Members Card ─────────────────────────────────────
// (Removed — team members now shown in project goal banner)

// ── SPA Client-Side Navigation (no page reload, no re-fetch) ─
function navigateToPage(projectId, page) {
  // Update URL without reloading
  const url = `project_dashboard.html?project=${projectId}&page=${page}`;
  history.pushState({ projectId, page }, '', url);

  // Re-render everything from cached data (zero API calls)
  renderProjectGoal();
  renderProjectSummary();
  updatePageTitle(projectId);
  applyPageRouting();

  // Re-render sidebar active states
  rerenderRailActiveStates(projectId, page);

  // If switching to overview, rebuild timeline + sprint panel
  if (page === 'overview') {
    document.getElementById('topbarSub').textContent = `${SPRINTS.length} sprints`;
    loadProjectTicketStats();
    buildTimeline();
    if (SPRINTS.length) {
      activeSprint = null; // force re-render
      selectSprint((SPRINTS.find(s => s.status === 'current') || SPRINTS[0]).id);
    }
  }
}
window.navigateToPage = navigateToPage;

function rerenderRailActiveStates(projectId, page) {
  // Update active project + sub-link highlights without rebuilding the DOM
  document.querySelectorAll('.prj-item').forEach((el, i) => {
    const p = projectsCache[i];
    if (!p) return;
    const isActive = p.id === projectId;
    el.classList.toggle('active-prj', isActive);
    const subLinks = el.nextElementSibling;
    if (subLinks && subLinks.classList.contains('prj-sub-links')) {
      subLinks.classList.toggle('expanded', isActive);
      const links = subLinks.querySelectorAll('.prj-sub-link');
      links.forEach(a => a.classList.remove('active-sub'));
      if (isActive) {
        const activeLink = page === 'integrations' ? links[1] : links[0];
        if (activeLink) activeLink.classList.add('active-sub');
      }
    }
  });
}

// Handle browser back/forward buttons
window.addEventListener('popstate', (e) => {
  if (e.state && e.state.projectId) {
    const { projectId, page } = e.state;
    renderProjectGoal();
    renderProjectSummary();
    updatePageTitle(projectId);
    applyPageRouting();
    rerenderRailActiveStates(projectId, page || 'overview');
    if ((page || 'overview') === 'overview') {
      buildTimeline();
      if (SPRINTS.length) {
        activeSprint = null;
        selectSprint((SPRINTS.find(s => s.status === 'current') || SPRINTS[0]).id);
      }
    }
  }
});

// ── Update page title with project name ──────────────────────
function updatePageTitle(pid) {
  if (!pid && projectsCache.length) pid = projectsCache[0].id;
  const project = projectsCache.find(p => p.id === pid);
  const titleEl = document.querySelector('.page-title');
  const pageSuffix = isIntegrationsPage() ? 'Integrations' : 'Overview';
  if (titleEl && project) {
    titleEl.textContent = project.name + ' ' + pageSuffix;
    document.title = 'EX-CDI — ' + project.name + ' ' + pageSuffix;
  }
}

// Also try to set title from URL on initial load (before API returns)
(function() {
  const pid = new URLSearchParams(window.location.search).get('project');
  if (pid) {
    // Will be updated properly once API data loads
    const titleEl = document.querySelector('.page-title');
    if (titleEl) titleEl.textContent = 'Loading project...';
  }
})();

// ── Expose functions to global scope (needed for inline onclick in ES modules) ──
window.showProjectFlyout = showProjectFlyout;
window.hideProjectFlyout = hideProjectFlyout;
window.sTab = sTab;
window.oIt = oIt;
window.selectSprint = selectSprint;
window.loadDecisions = loadDecisions;
window.decisionsLoaded = false;
window.setDtlView = setDtlView;
window.setDtlFilter = setDtlFilter;
window.loadTickets = loadTickets;
window.ticketsLoaded = false;
window.setTktView = setTktView;
window.setTktFilter = setTktFilter;
window.openMeetingPopup = openMeetingPopup;
window.closeMeetingPopup = closeMeetingPopup;
window.loadSprintMeetings = loadSprintMeetings;
window.loadSprintMeetings = loadSprintMeetings;
// ── Project Goal / Overview Banner ───────────────────────────
function renderProjectGoal() {
  const banner = document.getElementById('projectGoalBanner');
  if (!banner) return;
  const pid = new URLSearchParams(window.location.search).get('project');
  const project = projectsCache.find(p => p.id === pid) || projectsCache[0];
  if (!project || !project.description) { banner.style.display = 'none'; return; }

  const startFmt = project.start_date ? new Date(project.start_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '';
  const endFmt = project.target_end_date ? new Date(project.target_end_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '';
  const dateRange = startFmt && endFmt ? `${startFmt} — ${endFmt}` : '';

  const members = project.team_members || [];
  const owner = project.owner || '';
  const teamToggle = members.length ? `
      <button class="pg-team-toggle" onclick="document.getElementById('projectGoalBanner').querySelector('.pg-team').classList.toggle('open')">
        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        <span>Team (${members.length})</span>
        <svg class="pg-chevron" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
      </button>` : '';

  const teamList = members.length ? `
    <div class="pg-team">
      <div class="pg-team-list">
        ${members.map(m => {
          const initials = m.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
          const isOwner = m === owner;
          return `<span class="pg-member${isOwner ? ' pg-member--owner' : ''}"><span class="pg-member-av">${initials}</span>${esc(m)}${isOwner ? '<span class="pg-owner-badge">Owner</span>' : ''}</span>`;
        }).join('')}
      </div>
    </div>` : '';

  banner.innerHTML = `
    <div class="pg-header-row">
      <div class="pg-label">Project Goal</div>
      ${teamToggle}
    </div>
    <div class="pg-text">${esc(project.description)}</div>
    ${teamList}
  `;
  banner.style.display = '';
}
window.renderProjectGoal = renderProjectGoal;

// ── Project Summary Banner ───────────────────────────────────
function renderProjectSummary() {
  const banner = document.getElementById('projectSummaryBanner');
  if (!banner) return;
  const pid = new URLSearchParams(window.location.search).get('project');
  const project = projectsCache.find(p => p.id === pid) || projectsCache[0];
  if (!project) { banner.style.display = 'none'; return; }

  const status = (project.status || 'active').replace(/_/g, ' ');
  const statusCls = (project.status || 'active').toLowerCase().replace(/\s+/g, '_');

  const startFmt = project.start_date ? new Date(project.start_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : null;
  const endFmt = project.target_end_date ? new Date(project.target_end_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : null;

  const members = project.team_members || [];
  const owner = project.owner || null;
  const epicKey = project.epic_key || null;
  const jiraKey = project.jira_project_key || null;
  const repo = project.github_repo || null;
  const confluence = project.confluence_space_key || null;
  const tags = project.tags ? (typeof project.tags === 'string' ? project.tags.split(',').map(t => t.trim()) : project.tags) : [];
  const description = project.description || null;

  // Build a flowing prose summary
  let sentences = [];

  // Project name + description
  if (description) {
    sentences.push(`<strong>${esc(project.name)}</strong> is ${esc(description.charAt(0).toLowerCase() + description.slice(1))}`);
  } else {
    sentences.push(`<strong>${esc(project.name)}</strong> is currently <strong>${esc(status)}</strong>.`);
  }

  // Owner & team
  if (owner && members.length) {
    sentences.push(`The project is owned by <strong>${esc(owner)}</strong> and has a team of <strong>${members.length}</strong> member${members.length !== 1 ? 's' : ''}: ${members.map(m => esc(m)).join(', ')}.`);
  } else if (owner) {
    sentences.push(`The project is owned by <strong>${esc(owner)}</strong>.`);
  } else if (members.length) {
    sentences.push(`The team consists of <strong>${members.length}</strong> member${members.length !== 1 ? 's' : ''}: ${members.map(m => esc(m)).join(', ')}.`);
  }

  // Timeline
  if (startFmt && endFmt) {
    sentences.push(`It runs from <strong>${startFmt}</strong> to <strong>${endFmt}</strong>.`);
  } else if (startFmt) {
    sentences.push(`It started on <strong>${startFmt}</strong>.`);
  }

  // Integrations
  const integrations = [];
  if (jiraKey) integrations.push(`Jira project <strong>${esc(jiraKey)}</strong>`);
  if (epicKey) integrations.push(`epic <strong>${esc(epicKey)}</strong>`);
  if (repo) integrations.push(`GitHub repository <strong>${esc(repo)}</strong>`);
  if (confluence) integrations.push(`Confluence space <strong>${esc(confluence)}</strong>`);
  if (integrations.length) {
    sentences.push(`The project is tracked through ${integrations.join(', ')}.`);
  }

  // Tags
  if (tags.length) {
    sentences.push(`Tagged as: ${tags.map(t => `<span class="ps-tag">${esc(t)}</span>`).join(' ')}.`);
  }

  banner.innerHTML = `
    <div class="ps-header">
      <div class="ps-label">
        <svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
        Project Summary
      </div>
      <span class="ps-status s-${statusCls}">${esc(status)}</span>
    </div>
    <div class="ps-text">${sentences.join(' ')}</div>
  `;
  banner.style.display = '';
}
window.renderProjectSummary = renderProjectSummary;

// ── Integrations Page (inline within dashboard) ──────────────
let igTicketsData = [];
let igPagesData = [];
let igCommitsData = [];
let igCurrentSection = null;

function isIntegrationsPage() {
  return new URLSearchParams(window.location.search).get('page') === 'integrations';
}

// Toggle between overview and integrations content
function applyPageRouting() {
  const isIg = isIntegrationsPage();
  const overviewEl = document.getElementById('overviewContent');
  const igEl = document.getElementById('integrationsContent');
  if (overviewEl) overviewEl.style.display = isIg ? 'none' : '';
  if (igEl) igEl.style.display = isIg ? '' : 'none';
  if (isIg) loadIntegrationsData();
}

async function loadIntegrationsData() {
  const pid = new URLSearchParams(window.location.search).get('project');
  const project = projectsCache.find(p => p.id === pid) || projectsCache[0];

  // Set external links
  if (project) {
    if (project.jira_project_key) {
      const el = document.getElementById('jiraDashboardLink');
      if (el) { el.href = `https://your-domain.atlassian.net/jira/software/projects/${project.jira_project_key}/board`; }
    }
    if (project.confluence_space_key) {
      const el = document.getElementById('confluenceLink');
      if (el) { el.href = `https://your-domain.atlassian.net/wiki/spaces/${project.confluence_space_key}`; }
    }
    if (project.github_repo) {
      const el = document.getElementById('githubRepoLink');
      if (el) { el.href = `https://github.com/${project.github_repo}`; }
    }
  }

  await Promise.all([loadIgJira(), loadIgConfluence(), loadIgGithub()]);
  setupIgSearch();
}

async function loadIgJira() {
  try {
    igTicketsData = await fetchTicketsOnce();
    const completed = igTicketsData.filter(t => ['done','closed','resolved','complete','completed'].includes(t.status?.toLowerCase())).length;
    const inProgress = igTicketsData.filter(t => ['in progress','in review','in development'].includes(t.status?.toLowerCase())).length;
    const blockers = igTicketsData.filter(t => t.priority?.toLowerCase() === 'highest' || t.priority?.toLowerCase() === 'critical').length;
    const el = (id) => document.getElementById(id);
    el('jiraTotalTickets').textContent = igTicketsData.length;
    el('jiraCompleted').textContent = completed;
    el('jiraInProgress').textContent = inProgress;
    el('jiraBlockers').textContent = blockers;
  } catch (e) { console.warn('Jira load error:', e); }
}

async function loadIgConfluence() {
  try {
    const res = await fetch('/api/pages/');
    const data = await res.json();
    igPagesData = Array.isArray(data) ? data : (data.results || []);
    const spaces = new Set(igPagesData.map(p => p.space).filter(Boolean));
    const authors = new Set(igPagesData.map(p => p.author).filter(Boolean));
    const latest = igPagesData.length
      ? igPagesData.reduce((a, b) => new Date(b.page_updated_date || 0) > new Date(a.page_updated_date || 0) ? b : a)
      : null;
    const el = (id) => document.getElementById(id);
    el('confTotalPages').textContent = igPagesData.length;
    el('confSpaces').textContent = spaces.size;
    el('confAuthors').textContent = authors.size;
    el('confLatest').textContent = latest ? igFmtDate(latest.page_updated_date) : '—';
  } catch (e) { console.warn('Confluence load error:', e); }
}

async function loadIgGithub() {
  try {
    const res = await fetch('/api/commits/');
    const data = await res.json();
    igCommitsData = Array.isArray(data) ? data : (data.results || []);
    const contributors = new Set(igCommitsData.map(c => c.author_name).filter(Boolean));
    const totalFiles = igCommitsData.reduce((sum, c) => sum + (c.files?.length || 0), 0);
    const latest = igCommitsData.length
      ? igCommitsData.reduce((a, b) => new Date(b.commit_date || 0) > new Date(a.commit_date || 0) ? b : a)
      : null;
    const el = (id) => document.getElementById(id);
    el('ghTotalCommits').textContent = igCommitsData.length;
    el('ghContributors').textContent = contributors.size;
    el('ghFilesChanged').textContent = totalFiles;
    el('ghLatest').textContent = latest ? igFmtDate(latest.commit_date) : '—';
  } catch (e) { console.warn('GitHub load error:', e); }
}

function showIgSection(type) {
  igCurrentSection = type;
  const section = document.getElementById('igDetailSection');
  const title = document.getElementById('igDetailTitle');
  const filter = document.getElementById('igFilter');
  const search = document.getElementById('igSearch');
  search.value = '';
  document.querySelectorAll('.ig-card').forEach(c => c.classList.remove('active'));
  document.querySelector(`.ig-card[data-source="${type}"]`)?.classList.add('active');
  filter.innerHTML = '<option value="all">All</option>';

  if (type === 'jira') {
    title.textContent = 'Jira Tickets';
    [...new Set(igTicketsData.map(t => t.status).filter(Boolean))].sort().forEach(s =>
      filter.innerHTML += `<option value="${esc(s)}">${esc(s)}</option>`);
    renderIgJiraTable(igTicketsData);
  } else if (type === 'confluence') {
    title.textContent = 'Confluence Pages';
    [...new Set(igPagesData.map(p => p.space).filter(Boolean))].sort().forEach(s =>
      filter.innerHTML += `<option value="${esc(s)}">${esc(s)}</option>`);
    renderIgConfluenceGrid(igPagesData);
  } else if (type === 'github') {
    title.textContent = 'GitHub Commits';
    [...new Set(igCommitsData.map(c => c.author_name).filter(Boolean))].sort().forEach(a =>
      filter.innerHTML += `<option value="${esc(a)}">${esc(a)}</option>`);
    renderIgCommitsTable(igCommitsData);
  }
  section.classList.add('open');
  setTimeout(() => section.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

function hideIgSection() {
  document.getElementById('igDetailSection').classList.remove('open');
  document.querySelectorAll('.ig-card').forEach(c => c.classList.remove('active'));
  igCurrentSection = null;
}

function setupIgSearch() {
  const search = document.getElementById('igSearch');
  const filter = document.getElementById('igFilter');
  if (!search || !filter) return;
  const doFilter = () => {
    if (!igCurrentSection) return;
    const q = search.value.toLowerCase().trim();
    const f = filter.value;
    if (igCurrentSection === 'jira') {
      let items = igTicketsData;
      if (f !== 'all') items = items.filter(t => t.status === f);
      if (q) items = items.filter(t => (t.issue_key||'').toLowerCase().includes(q) || (t.summary||'').toLowerCase().includes(q) || (t.assignee||'').toLowerCase().includes(q));
      renderIgJiraTable(items);
    } else if (igCurrentSection === 'confluence') {
      let items = igPagesData;
      if (f !== 'all') items = items.filter(p => p.space === f);
      if (q) items = items.filter(p => (p.title||'').toLowerCase().includes(q) || (p.author||'').toLowerCase().includes(q));
      renderIgConfluenceGrid(items);
    } else if (igCurrentSection === 'github') {
      let items = igCommitsData;
      if (f !== 'all') items = items.filter(c => c.author_name === f);
      if (q) items = items.filter(c => (c.sha||'').toLowerCase().includes(q) || (c.message||'').toLowerCase().includes(q) || (c.author_name||'').toLowerCase().includes(q));
      renderIgCommitsTable(items);
    }
  };
  search.addEventListener('input', doFilter);
  filter.addEventListener('change', doFilter);
}

function renderIgJiraTable(tickets) {
  const body = document.getElementById('igDetailBody');
  if (!tickets.length) { body.innerHTML = '<div class="ig-empty">No tickets found</div>'; return; }
  body.innerHTML = `<table class="ig-table"><thead><tr><th>Key</th><th>Type</th><th>Summary</th><th>Status</th><th>Priority</th><th>Assignee</th><th>Story Pts</th><th>Updated</th></tr></thead><tbody>${tickets.map(t => `<tr><td class="cell-key">${esc(t.issue_key)}</td><td class="cell-meta">${esc(t.issue_type)}</td><td class="cell-summary" title="${esc(t.summary)}">${esc(t.summary)}</td><td>${igStatusBadge(t.status)}</td><td>${igPriorityBadge(t.priority)}</td><td class="cell-meta">${esc(t.assignee||'—')}</td><td class="cell-meta" style="text-align:center">${t.story_points??'—'}</td><td class="cell-meta">${igFmtDate(t.updated_date)}</td></tr>`).join('')}</tbody></table>`;
}

function renderIgConfluenceGrid(pages) {
  const body = document.getElementById('igDetailBody');
  if (!pages.length) { body.innerHTML = '<div class="ig-empty">No pages found</div>'; return; }
  body.innerHTML = `<div class="ig-page-grid">${pages.map(p => `<div class="ig-page-card"><div class="ig-page-card-title">${esc(p.title)}</div><div class="ig-page-card-meta"><span>Space: ${esc(p.space||'—')}</span><span>Author: ${esc(p.author||'—')}</span><span>v${p.version||1}</span><span>${igFmtDate(p.page_updated_date)}</span></div>${(p.labels&&p.labels.length)?`<div class="ig-page-labels">${p.labels.map(l=>`<span class="ig-page-label">${esc(l)}</span>`).join('')}</div>`:''}</div>`).join('')}</div>`;
}

function renderIgCommitsTable(commits) {
  const body = document.getElementById('igDetailBody');
  if (!commits.length) { body.innerHTML = '<div class="ig-empty">No commits found</div>'; return; }
  body.innerHTML = `<table class="ig-table"><thead><tr><th>SHA</th><th>Message</th><th>Author</th><th>Files</th><th>Changes</th><th>Date</th></tr></thead><tbody>${commits.map(c => {
    const adds = (c.files||[]).reduce((s,f)=>s+(f.additions||0),0);
    const dels = (c.files||[]).reduce((s,f)=>s+(f.deletions||0),0);
    return `<tr><td><span class="ig-commit-sha">${esc((c.sha||'').substring(0,7))}</span></td><td class="ig-commit-msg" title="${esc(c.message)}">${esc((c.message||'').substring(0,60))}${(c.message||'').length>60?'...':''}</td><td class="cell-meta">${esc(c.author_name)}</td><td class="ig-commit-files">${(c.files||[]).length} file${(c.files||[]).length!==1?'s':''}</td><td class="cell-meta"><span class="ig-commit-additions">+${adds}</span> <span class="ig-commit-deletions">-${dels}</span></td><td class="cell-meta">${igFmtDate(c.commit_date)}</td></tr>`;
  }).join('')}</tbody></table>`;
}

function igStatusBadge(status) {
  if (!status) return '<span class="ig-badge todo">—</span>';
  const s = status.toLowerCase();
  let cls = 'todo';
  if (['done','closed','resolved','complete','completed'].includes(s)) cls = 'done';
  else if (['in progress','in development'].includes(s)) cls = 'in-progress';
  else if (['blocked','impediment'].includes(s)) cls = 'blocked';
  else if (['in review','review','code review'].includes(s)) cls = 'review';
  return `<span class="ig-badge ${cls}">${esc(status)}</span>`;
}

function igPriorityBadge(priority) {
  if (!priority) return '<span class="cell-meta">—</span>';
  return `<span class="ig-priority ${priority.toLowerCase()}"><span class="ig-priority-dot"></span>${esc(priority)}</span>`;
}

function igFmtDate(d) {
  if (!d) return '—';
  try { return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); } catch { return '—'; }
}

// Expose integrations functions for onclick
window.showIgSection = showIgSection;
window.hideIgSection = hideIgSection;

// ── New Integration Modal ────────────────────────────────────
const NI_BRANDS = {
  zoom:        { name: 'Zoom',             cls: 'zoom',    svg: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h10a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm12 3l6-3v12l-6-3V7z"/></svg>' },
  'google-meet': { name: 'Google Meet',    cls: 'gmeet',   svg: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M14 12l5-3.5V5a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3.5l-5-3.5zm-4 4H6v-2h4v2zm0-4H6V10h4v2z"/></svg>' },
  slack:       { name: 'Slack',            cls: 'slack',   svg: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52z"/></svg>' },
  teams:       { name: 'Microsoft Teams',  cls: 'teams',   svg: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.35 8.5c-.2 0-.39.03-.57.08A3.5 3.5 0 0 0 15.5 5c-.26 0-.5.03-.74.08A4 4 0 0 0 7.5 4C5.57 4 4 5.57 4 7.5c0 .26.03.5.08.74A3.5 3.5 0 0 0 5.5 15H9v5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-5h4.35a2.65 2.65 0 0 0 0-5.3V8.5z"/></svg>' },
  outlook:     { name: 'Outlook Calendar', cls: 'outlook', svg: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5zm4 0v2h10V5H7zm-1 4v8h12V9H6zm2 2h3v3H8v-3z"/></svg>' },
  trello:      { name: 'Trello',           cls: 'trello',  svg: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="2" y="2" width="20" height="20" rx="3" ry="3" fill="none" stroke="currentColor" stroke-width="2"/><rect x="5" y="5" width="5" height="12" rx="1"/><rect x="13" y="5" width="5" height="8" rx="1"/></svg>' },
};

let _currentIntService = null;

function openNewIntegrationModal() {
  document.getElementById('niModalOverlay').classList.add('visible');
  document.getElementById('niSearch').value = '';
  filterIntegrations('');
}
window.openNewIntegrationModal = openNewIntegrationModal;

function closeNewIntegrationModal() {
  document.getElementById('niModalOverlay').classList.remove('visible');
}
window.closeNewIntegrationModal = closeNewIntegrationModal;

function filterIntegrations(q) {
  q = q.toLowerCase().trim();
  document.querySelectorAll('#niGrid .ni-item').forEach(el => {
    const name = el.dataset.name.toLowerCase();
    el.classList.toggle('hidden', q !== '' && !name.includes(q));
  });
}
window.filterIntegrations = filterIntegrations;

function startIntegrationFlow(service) {
  closeNewIntegrationModal();
  _currentIntService = service;
  const brand = NI_BRANDS[service] || { name: service, cls: '', svg: '' };
  const iconEl = document.getElementById('niSigninIcon');
  iconEl.className = 'ni-signin-icon ni-icon ' + brand.cls;
  iconEl.innerHTML = brand.svg;
  document.getElementById('niSigninTitle').textContent = 'Connect ' + brand.name;
  document.getElementById('niSigninEmail').value = '';
  document.getElementById('niSigninPassword').value = '';
  const btn = document.getElementById('niSigninBtn');
  btn.textContent = 'Sign In & Connect';
  btn.classList.remove('success');
  btn.disabled = false;
  document.getElementById('niSigninOverlay').classList.add('visible');
}
window.startIntegrationFlow = startIntegrationFlow;

function closeSigninModal() {
  document.getElementById('niSigninOverlay').classList.remove('visible');
}
window.closeSigninModal = closeSigninModal;

function submitIntegration(e) {
  e.preventDefault();
  const btn = document.getElementById('niSigninBtn');
  const brand = NI_BRANDS[_currentIntService] || { name: _currentIntService };
  btn.textContent = 'Connecting...';
  btn.disabled = true;
  // Simulate OAuth / credential verification
  setTimeout(() => {
    btn.textContent = '\u2713 ' + brand.name + ' Connected!';
    btn.classList.add('success');
    // Auto-close after showing success
    setTimeout(() => closeSigninModal(), 1400);
  }, 1200);
}
window.submitIntegration = submitIntegration;

