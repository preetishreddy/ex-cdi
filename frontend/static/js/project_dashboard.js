/* ============================================================
   EX-CDI — Project Dashboard JavaScript
   ============================================================ */

// ── Sprint Data ──────────────────────────────────────────────
const SPRINTS = [
  {
    id: 's1', name: 'Sprint 1', status: 'completed',
    dates: ['2026-02-03', '2026-02-14'],
    issues: [
      { issue_key: 'ONBOARD-10', issue_type: 'Story', summary: 'Project scaffolding & CI/CD pipeline', status: 'Done', priority: 'High', assignee: 'Jordan Rivera', reporter: 'Sarah Mitchell', created_date: '2026-02-03T00:00:00Z', updated_date: '2026-02-07T00:00:00Z', resolved_date: '2026-02-07T00:00:00Z', labels: 'devops;infrastructure', epic_link: 'ONBOARD-1', story_points: 5, comments: '[2026-02-04 10:00 - Jordan Rivera] Initialized monorepo. Docker Compose for local dev.\n[2026-02-07 14:00 - Jordan Rivera] GitHub Actions CI pipeline live.' },
      { issue_key: 'ONBOARD-11', issue_type: 'Task', summary: 'Design system & component library', status: 'Done', priority: 'Medium', assignee: 'Lisa Park', reporter: 'Alex Kumar', created_date: '2026-02-03T00:00:00Z', updated_date: '2026-02-10T00:00:00Z', resolved_date: '2026-02-10T00:00:00Z', labels: 'frontend;design', epic_link: 'ONBOARD-1', story_points: 3, comments: '[2026-02-05 09:00 - Lisa Park] Tailwind + Storybook done.\n[2026-02-10 11:00 - Lisa Park] 12 base components published.' },
      { issue_key: 'ONBOARD-12', issue_type: 'Story', summary: 'User authentication & session management', status: 'Done', priority: 'Critical', assignee: 'Dave Rossi', reporter: 'Sarah Mitchell', created_date: '2026-02-04T00:00:00Z', updated_date: '2026-02-12T00:00:00Z', resolved_date: '2026-02-12T00:00:00Z', labels: 'backend;auth;security', epic_link: 'ONBOARD-1', story_points: 8, comments: '[2026-02-06 10:00 - Dave Rossi] JWT auth flow implemented.\n[2026-02-12 09:00 - Sarah Mitchell] Security review passed.' },
      { issue_key: 'ONBOARD-13', issue_type: 'Task', summary: 'Database schema design & seed data', status: 'Done', priority: 'High', assignee: 'Priya Lakshmi', reporter: 'Dave Rossi', created_date: '2026-02-03T00:00:00Z', updated_date: '2026-02-08T00:00:00Z', resolved_date: '2026-02-08T00:00:00Z', labels: 'database;backend', epic_link: 'ONBOARD-1', story_points: 5, comments: '[2026-02-05 15:00 - Priya Lakshmi] ERD finalized. 14 tables.\n[2026-02-08 10:00 - Priya Lakshmi] Alembic migrations + seed script.' }
    ],
    meetings: [
      { date: '2026-02-03', type: 'planning', name: 'Sprint 1 Planning', project: 'ONBOARD', time: '09:00–10:30', summary: 'Kicked off project. Defined architecture, assigned stories. 21 points committed.' },
      { date: '2026-02-07', type: 'review', name: 'Mid-Sprint Check', project: 'ONBOARD', time: '14:00–14:30', summary: 'CI/CD live. Auth in progress. Schema on track.' },
      { date: '2026-02-14', type: 'retro', name: 'Sprint 1 Retro', project: 'ONBOARD', time: '10:00–11:00', summary: 'All 21 points delivered. Velocity baseline set. Improvement: faster PR reviews.' }
    ],
    aiSummary: 'Sprint 1 established the project foundation. All <strong>21 story points delivered</strong>. CI/CD pipeline operational. JWT auth with SSO deployed. Database schema finalized (14 tables). Design system published with 12 components and dark theme.'
  },
  {
    id: 's2', name: 'Sprint 2', status: 'current',
    dates: ['2026-02-17', '2026-02-28'],
    issues: [
      { issue_key: 'ONBOARD-30', issue_type: 'Task', summary: 'Performance optimization for dashboard', status: 'Done', priority: 'Medium', assignee: 'Lisa Park', reporter: 'Dave Rossi', created_date: '2026-01-29T00:00:00Z', updated_date: '2026-01-30T00:00:00Z', resolved_date: '2026-01-30T00:00:00Z', labels: 'frontend;performance', epic_link: 'ONBOARD-10', story_points: 3, comments: '[2026-01-30 09:30 - Lisa Park] React.memo to prevent re-renders.\n[2026-01-30 16:30 - Dave Rossi] Fixed CONN_MAX_AGE.' },
      { issue_key: 'ONBOARD-31', issue_type: 'Story', summary: 'Real-time inventory alert system', status: 'In Progress', priority: 'High', assignee: 'Alex Kumar', reporter: 'Sarah Mitchell', created_date: '2026-02-20T00:00:00Z', updated_date: '2026-02-25T00:00:00Z', resolved_date: null, labels: 'backend;websocket', epic_link: 'ONBOARD-10', story_points: 5, comments: '[2026-02-22 10:00 - Alex Kumar] WebSocket server live.\n[2026-02-25 09:00 - Sarah Mitchell] Add retry logic for Slack.' },
      { issue_key: 'ONBOARD-32', issue_type: 'Bug', summary: 'Data warehouse migration — schema mismatch', status: 'Blocked', priority: 'Critical', assignee: 'Jordan Rivera', reporter: 'Priya Lakshmi', created_date: '2026-02-18T00:00:00Z', updated_date: '2026-02-26T00:00:00Z', resolved_date: null, labels: 'database;migration;blocker', epic_link: 'ONBOARD-10', story_points: 8, comments: '[2026-02-19 14:00 - Jordan Rivera] 3 date format variations.\n[2026-02-26 16:00 - Jordan Rivera] Transform handles 2/3 formats.' },
      { issue_key: 'ONBOARD-33', issue_type: 'Task', summary: 'Sales trend visualization component', status: 'In Review', priority: 'High', assignee: 'Lisa Park', reporter: 'Alex Kumar', created_date: '2026-02-21T00:00:00Z', updated_date: '2026-02-26T00:00:00Z', resolved_date: null, labels: 'frontend;charts', epic_link: 'ONBOARD-10', story_points: 5, comments: '[2026-02-23 09:00 - Lisa Park] Chart with zoom & pan.\n[2026-02-26 11:00 - Alex Kumar] Tooltip needs currency formatting.' },
      { issue_key: 'ONBOARD-34', issue_type: 'Story', summary: 'Prediction API for churn model', status: 'Done', priority: 'High', assignee: 'Priya Lakshmi', reporter: 'Sarah Mitchell', created_date: '2026-02-20T00:00:00Z', updated_date: '2026-02-27T00:00:00Z', resolved_date: '2026-02-27T00:00:00Z', labels: 'backend;ml;api', epic_link: 'ONBOARD-10', story_points: 5, comments: '[2026-02-22 10:00 - Priya Lakshmi] AUC: 0.87.\n[2026-02-27 09:00 - Sarah Mitchell] Approved for merge.' }
    ],
    meetings: [
      { date: '2026-02-17', type: 'planning', name: 'Sprint 2 Planning', project: 'ONBOARD', time: '09:00–10:30', summary: '26 story points committed. Dashboard perf and alerts prioritized. Mock data for ML.' },
      { date: '2026-02-18', type: 'standup', name: 'Daily Standup', project: 'ONBOARD', time: '09:00–09:15', summary: 'Jordan flagged schema mismatch. Priya confirmed mock data workaround.' },
      { date: '2026-02-21', type: 'review', name: 'Mid-Sprint Review', project: 'ONBOARD', time: '14:00–15:00', summary: 'ONBOARD-30 nearly done. WebSocket live. ONBOARD-32 still blocked.' },
      { date: '2026-02-25', type: 'standup', name: 'Daily Standup', project: 'ONBOARD', time: '09:00–09:15', summary: 'Lisa integrated date picker. Alex testing Slack retry. Prediction API approved.' },
      { date: '2026-02-27', type: 'review', name: 'Sprint 2 Demo', project: 'ONBOARD', time: '14:00–15:30', summary: 'Demoed perf gains, prediction API, sales chart. Blocker carries to Sprint 3.' },
      { date: '2026-02-28', type: 'retro', name: 'Sprint 2 Retro', project: 'ONBOARD', time: '10:00–11:00', summary: '21 of 26 pts delivered. Improvement: earlier blocker escalation.' }
    ],
    aiSummary: '<strong>Sprint 2</strong> has 5 issues totaling <strong>26 story points</strong>. <strong>2 completed</strong> (8 pts), 2 in progress, 1 blocked. Blocker: <strong>data warehouse schema mismatch</strong> — mock data approved. Perf optimization resolved. Prediction API live (AUC 0.87). Sales visualization in review.'
  },
  {
    id: 's3', name: 'Sprint 3', status: 'upcoming',
    dates: ['2026-03-02', '2026-03-13'],
    issues: [
      { issue_key: 'ONBOARD-40', issue_type: 'Story', summary: 'Customer segmentation dashboard', status: 'To Do', priority: 'High', assignee: 'Alex Kumar', reporter: 'Sarah Mitchell', created_date: '2026-02-28T00:00:00Z', updated_date: '2026-02-28T00:00:00Z', resolved_date: null, labels: 'frontend;dashboard', epic_link: 'ONBOARD-10', story_points: 8, comments: '' },
      { issue_key: 'ONBOARD-41', issue_type: 'Task', summary: 'Complete data warehouse migration', status: 'To Do', priority: 'Critical', assignee: 'Jordan Rivera', reporter: 'Priya Lakshmi', created_date: '2026-02-28T00:00:00Z', updated_date: '2026-02-28T00:00:00Z', resolved_date: null, labels: 'database;migration', epic_link: 'ONBOARD-10', story_points: 8, comments: '' },
      { issue_key: 'ONBOARD-42', issue_type: 'Story', summary: 'Email notification system', status: 'To Do', priority: 'Medium', assignee: 'Dave Rossi', reporter: 'Sarah Mitchell', created_date: '2026-02-28T00:00:00Z', updated_date: '2026-02-28T00:00:00Z', resolved_date: null, labels: 'backend;notifications', epic_link: 'ONBOARD-10', story_points: 5, comments: '' }
    ],
    meetings: [],
    aiSummary: '<strong>Sprint 3</strong> planned with 3 issues, <strong>21 story points</strong>. Focus: customer segmentation dashboard, completing warehouse migration from Sprint 2, and email notifications.'
  },
  {
    id: 's4', name: 'Sprint 4', status: 'upcoming',
    dates: ['2026-03-16', '2026-03-27'],
    issues: [], meetings: [],
    aiSummary: '<strong>Sprint 4</strong> backlog not yet groomed. Expected: production hardening, E2E testing, client demo prep.'
  }
];

// ── Constants ────────────────────────────────────────────────
const MO = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// ── State ────────────────────────────────────────────────────
let activeSprint = null;
let decisionsLoaded = false;
let decisionsData = [];

// ── User Setup ───────────────────────────────────────────────
const userEmail = sessionStorage.getItem('userEmail') || 'user@company.atlassian.net';
const jiraDomain = sessionStorage.getItem('jiraDomain') || 'company.atlassian.net';
const userName = userEmail.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

document.getElementById('sidebarUserName').textContent = userName;
document.getElementById('userAvatar').textContent = userName.split(' ').map(w => w[0]).join('').substring(0, 2);
document.getElementById('connectDetail').textContent = `${userEmail} → ${jiraDomain}`;

// ── Connection Animation ─────────────────────────────────────
setTimeout(() => {
  document.getElementById('step1').style.width = '100%';
  document.getElementById('connectTitle').textContent = 'Authenticating...';
}, 400);

setTimeout(() => {
  document.getElementById('step2').style.width = '100%';
  document.getElementById('connectTitle').textContent = 'Fetching sprints...';
}, 1200);

setTimeout(() => {
  document.getElementById('step3').style.width = '100%';
  document.getElementById('connectTitle').textContent = 'Loading project data...';
}, 2000);

setTimeout(() => {
  document.getElementById('connectBanner').classList.add('success');
  document.getElementById('connectTitle').textContent = 'Connected to Jira';
  document.getElementById('connectDetail').textContent = `ONBOARD · ${SPRINTS.length} sprints · ${SPRINTS.reduce((s, sp) => s + sp.issues.length, 0)} issues`;
  document.getElementById('connectStatus').innerHTML = '<div class="dot" style="background:var(--success);animation:pulse 1.5s infinite"></div><span style="color:var(--success)">Connected</span>';
  document.getElementById('topbarSub').textContent = `ONBOARD · ${SPRINTS.length} sprints`;
  document.getElementById('navBadge').textContent = SPRINTS.reduce((s, sp) => s + sp.issues.length, 0);
  buildTimeline();
  selectSprint((SPRINTS.find(s => s.status === 'current') || SPRINTS[0]).id);
}, 2800);

// ── Helpers ──────────────────────────────────────────────────
function fmtR(s, e) {
  const a = new Date(s), b = new Date(e);
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
    const pts = sp.issues.reduce((s, i) => s + (i.story_points || 0), 0);
    const dp = sp.issues.filter(i => i.status === 'Done').reduce((s, i) => s + (i.story_points || 0), 0);
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
        <div class="tl-pts">${pts > 0 ? dp + '/' + pts + ' pts' : 'TBD'}</div>
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
  const is = sp.issues;
  const dn = is.filter(i => i.status === 'Done');
  const bl = is.filter(i => i.status === 'Blocked');
  const tp = is.reduce((s, i) => s + (i.story_points || 0), 0);
  const dpn = dn.reduce((s, i) => s + (i.story_points || 0), 0);
  const as = [...new Set(is.map(i => i.assignee))];

  p.innerHTML = `
    <div class="detail-header">
      <div class="detail-icon"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
      <div>
        <div class="detail-title">${sp.name} — ONBOARD</div>
        <div class="detail-sub">${fmtR(sp.dates[0], sp.dates[1])} · ${is.length} issues · ${as.length} members</div>
      </div>
      <div class="detail-stats">
        <div class="detail-stat"><div class="detail-stat-val" style="color:var(--accent)">${tp}</div><div class="detail-stat-label">Points</div></div>
        <div class="detail-stat"><div class="detail-stat-val" style="color:var(--success)">${dpn}</div><div class="detail-stat-label">Completed</div></div>
        <div class="detail-stat"><div class="detail-stat-val" style="color:var(--danger)">${bl.length}</div><div class="detail-stat-label">Blocked</div></div>
      </div>
    </div>

    <div class="tabs-strip">
      <div class="tab-item active" onclick="sTab('dp','summary',this)"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>AI Summary</div>
      <div class="tab-item" onclick="sTab('dp','meetings',this)"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>Meetings</div>
      <div class="tab-item" onclick="sTab('dp','outcomes',this)"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>Outcomes</div>
      <div class="tab-item" onclick="sTab('dp','issues',this)"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>All Issues</div>
      <div class="tab-item" onclick="sTab('dp','decisions',this);loadDecisions()"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>Decisions</div>
    </div>

    <div class="tab-content active" id="dp-summary">
      <div class="ai-summary-box">
        <div class="ai-label"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 6v6l4 2"/><circle cx="18" cy="6" r="3" fill="currentColor" stroke="none"/></svg><span class="ai-dot"></span>AI Sprint Summary</div>
        <div class="ai-summary-text">${sp.aiSummary}</div>
      </div>
      <div class="stat-mini-grid">
        <div class="stat-mini"><div class="stat-mini-val" style="color:var(--accent)">${tp}</div><div class="stat-mini-label">Story Points</div></div>
        <div class="stat-mini"><div class="stat-mini-val" style="color:var(--warn)">${bl.length}</div><div class="stat-mini-label">Blockers</div></div>
        <div class="stat-mini"><div class="stat-mini-val" style="color:var(--success)">${dn.length}/${is.length}</div><div class="stat-mini-label">Completed</div></div>
      </div>
      ${as.length
        ? `<div class="section-sub">Team</div><div class="participants">${as.map(n =>
            `<div class="participant"><div class="part-avatar" style="background:${gr(n)}">${ini(n)}</div><div><div class="part-name">${n}</div><div class="part-role">${rl(n, is)}</div></div></div>`
          ).join('')}</div>`
        : '<p style="color:var(--muted);font-size:13px">No team assigned yet.</p>'
      }
    </div>

    <div class="tab-content" id="dp-meetings">${bCal(sp)}</div>

    <div class="tab-content" id="dp-outcomes">
      ${is.length
        ? `<div class="outcome-list">${is.map(i => oIt(i)).join('')}</div>`
        : '<p style="color:var(--muted);font-size:13px">No issues yet.</p>'
      }
    </div>

    <div class="tab-content" id="dp-issues">
      ${is.length
        ? `<table class="decisions-table"><thead><tr><th>Issue</th><th>Summary</th><th>Assignee</th><th>Pts</th><th>Status</th></tr></thead><tbody>${is.map(i =>
            `<tr><td style="font-family:var(--font-mono);font-size:12px;color:var(--muted)">${i.issue_key}</td><td>${i.summary}</td><td>${i.assignee}</td><td style="text-align:center">${i.story_points}</td><td><span class="status-pill ${pCl(i.status)}">${i.status}</span></td></tr>`
          ).join('')}</tbody></table>`
        : '<p style="color:var(--muted);font-size:13px">Backlog not groomed.</p>'
      }
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
}

// ── Calendar Builder ─────────────────────────────────────────
function bCal(sp) {
  if (!sp.meetings.length) return '<p style="color:var(--muted);font-size:13px;padding:4px">No meetings scheduled.</p>';

  const st = new Date(sp.dates[0]), en = new Date(sp.dates[1]);
  const yr = st.getFullYear(), mo = st.getMonth();
  const fd = new Date(yr, mo, 1).getDay(), dm = new Date(yr, mo + 1, 0).getDate();
  const mm = {};
  sp.meetings.forEach(m => { mm[m.date] = m; });
  const td = new Date().toISOString().split('T')[0];

  let h = `<div class="cal-month"><svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>${MO[mo]} ${yr}</div><div class="cal-grid">`;

  ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(d => {
    h += `<div class="cal-head">${d}</div>`;
  });

  for (let i = 0; i < fd; i++) h += '<div class="cal-day"></div>';

  for (let d = 1; d <= dm; d++) {
    const ds = `${yr}-${String(mo + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const dO = new Date(yr, mo, d);
    const iS = dO >= st && dO <= en;
    const iT = ds === td;
    const m = mm[ds];
    let c = 'cal-day';
    if (iS) c += ' in-sprint';
    if (iT) c += ' today';
    if (m) c += ` has-meeting type-${m.type}`;

    let tt = '';
    if (m) {
      const tc = m.type === 'standup' ? 'var(--success)' : m.type === 'retro' ? 'var(--warn)' : m.type === 'review' ? 'var(--accent2)' : 'var(--accent)';
      tt = `<div class="cal-tooltip"><div class="tt-type" style="color:${tc}"><div class="tt-dot" style="background:${tc}"></div>${m.type.charAt(0).toUpperCase() + m.type.slice(1)}</div><div class="tt-name">${m.name}</div><div class="tt-project">${m.project} · ${m.time}</div><div class="tt-summary">${m.summary}</div></div>`;
    }

    h += `<div class="${c}">${d}${tt}</div>`;
  }

  h += '</div><div class="cal-legend"><div class="cal-legend-item"><div class="cal-legend-dot" style="background:var(--accent)"></div>Planning</div><div class="cal-legend-item"><div class="cal-legend-dot" style="background:var(--success)"></div>Standup</div><div class="cal-legend-item"><div class="cal-legend-dot" style="background:var(--accent2)"></div>Review</div><div class="cal-legend-item"><div class="cal-legend-dot" style="background:var(--warn)"></div>Retro</div></div>';
  return h;
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

// ── Export ────────────────────────────────────────────────────
function exportData() {
  const d = SPRINTS.find(s => s.id === activeSprint);
  if (!d) return;
  const b = new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' });
  const u = URL.createObjectURL(b);
  const a = document.createElement('a');
  a.href = u;
  a.download = d.name.replace(/\s/g, '-').toLowerCase() + '-export.json';
  a.click();
  URL.revokeObjectURL(u);
}

// ── Decisions API Integration ────────────────────────────────
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
    .then(data => {
      decisionsLoaded = true;
      decisionsData = Array.isArray(data) ? data : (data.results || []);
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

// ── Expose functions to global scope (needed for inline onclick in ES modules) ──
window.sTab = sTab;
window.oIt = oIt;
window.selectSprint = selectSprint;
window.exportData = exportData;
window.loadDecisions = loadDecisions;
window.decisionsLoaded = false;
window.setDtlView = setDtlView;
window.setDtlFilter = setDtlFilter;
