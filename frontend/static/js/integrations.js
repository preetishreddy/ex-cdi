/* ============================================================
   LightHouse — Integrations Page Logic
   ============================================================ */

const API = '/api';

// ── State ───────────────────────────────────────────────────
let ticketsData = [];
let pagesData = [];
let commitsData = [];
let projectData = null;
let currentSection = null;

// ── Init ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await loadProjectData();
  await Promise.all([loadJiraData(), loadConfluenceData(), loadGithubData()]);
  setupSearch();
});

// ── Load project info (for links) ───────────────────────────
async function loadProjectData() {
  try {
    const res = await fetch(`${API}/projects/`);
    const data = await res.json();
    const projects = Array.isArray(data) ? data : (data.results || []);
    if (projects.length) {
      projectData = projects[0];
      // Set external links
      if (projectData.jira_project_key) {
        const jiraLink = document.getElementById('jiraDashboardLink');
        jiraLink.href = `https://your-domain.atlassian.net/jira/software/projects/${projectData.jira_project_key}/board`;
        jiraLink.title = `Open ${projectData.jira_project_key} Jira board`;
      }
      if (projectData.confluence_space_key) {
        const confLink = document.getElementById('confluenceLink');
        confLink.href = `https://your-domain.atlassian.net/wiki/spaces/${projectData.confluence_space_key}`;
        confLink.title = `Open ${projectData.confluence_space_key} space`;
      }
      if (projectData.github_repo) {
        const ghLink = document.getElementById('githubRepoLink');
        ghLink.href = `https://github.com/${projectData.github_repo}`;
        ghLink.title = `Open ${projectData.github_repo}`;
      }
    }
  } catch (e) {
    console.warn('Could not load project data:', e);
  }
}

// ── Jira ────────────────────────────────────────────────────
async function loadJiraData() {
  try {
    const res = await fetch(`${API}/tickets/`);
    const data = await res.json();
    ticketsData = Array.isArray(data) ? data : (data.results || []);

    const completed = ticketsData.filter(t => ['done','closed','resolved','complete','completed'].includes(t.status?.toLowerCase())).length;
    const inProgress = ticketsData.filter(t => ['in progress','in review','in development'].includes(t.status?.toLowerCase())).length;
    const blockers = ticketsData.filter(t => t.priority?.toLowerCase() === 'highest' || t.priority?.toLowerCase() === 'critical').length;

    document.getElementById('jiraTotalTickets').textContent = ticketsData.length;
    document.getElementById('jiraCompleted').textContent = completed;
    document.getElementById('jiraInProgress').textContent = inProgress;
    document.getElementById('jiraBlockers').textContent = blockers;
  } catch (e) {
    console.warn('Could not load Jira data:', e);
  }
}

// ── Confluence ──────────────────────────────────────────────
async function loadConfluenceData() {
  try {
    const res = await fetch(`${API}/pages/`);
    const data = await res.json();
    pagesData = Array.isArray(data) ? data : (data.results || []);

    const spaces = new Set(pagesData.map(p => p.space).filter(Boolean));
    const authors = new Set(pagesData.map(p => p.author).filter(Boolean));
    const latest = pagesData.length
      ? pagesData.reduce((a, b) => new Date(b.page_updated_date || 0) > new Date(a.page_updated_date || 0) ? b : a)
      : null;

    document.getElementById('confTotalPages').textContent = pagesData.length;
    document.getElementById('confSpaces').textContent = spaces.size;
    document.getElementById('confAuthors').textContent = authors.size;
    document.getElementById('confLatest').textContent = latest
      ? fmtDate(latest.page_updated_date)
      : '—';
  } catch (e) {
    console.warn('Could not load Confluence data:', e);
  }
}

// ── GitHub ──────────────────────────────────────────────────
async function loadGithubData() {
  try {
    const res = await fetch(`${API}/commits/`);
    const data = await res.json();
    commitsData = Array.isArray(data) ? data : (data.results || []);

    const contributors = new Set(commitsData.map(c => c.author_name).filter(Boolean));
    const totalFiles = commitsData.reduce((sum, c) => sum + (c.files?.length || 0), 0);
    const latest = commitsData.length
      ? commitsData.reduce((a, b) => new Date(b.commit_date || 0) > new Date(a.commit_date || 0) ? b : a)
      : null;

    document.getElementById('ghTotalCommits').textContent = commitsData.length;
    document.getElementById('ghContributors').textContent = contributors.size;
    document.getElementById('ghFilesChanged').textContent = totalFiles;
    document.getElementById('ghLatest').textContent = latest
      ? fmtDate(latest.commit_date)
      : '—';
  } catch (e) {
    console.warn('Could not load GitHub data:', e);
  }
}

// ── Show / Hide Detail Section ──────────────────────────────
function showSection(type) {
  currentSection = type;
  const section = document.getElementById('igDetailSection');
  const title = document.getElementById('igDetailTitle');
  const filter = document.getElementById('igFilter');
  const search = document.getElementById('igSearch');
  search.value = '';

  // Highlight active card
  document.querySelectorAll('.ig-card').forEach(c => c.classList.remove('active'));
  document.querySelector(`.ig-card[data-source="${type}"]`)?.classList.add('active');

  // Configure filter
  filter.innerHTML = '<option value="all">All</option>';

  if (type === 'jira') {
    title.textContent = 'Jira Tickets';
    const statuses = [...new Set(ticketsData.map(t => t.status).filter(Boolean))].sort();
    statuses.forEach(s => {
      filter.innerHTML += `<option value="${esc(s)}">${esc(s)}</option>`;
    });
    renderJiraTable(ticketsData);
  } else if (type === 'confluence') {
    title.textContent = 'Confluence Pages';
    const spaces = [...new Set(pagesData.map(p => p.space).filter(Boolean))].sort();
    spaces.forEach(s => {
      filter.innerHTML += `<option value="${esc(s)}">${esc(s)}</option>`;
    });
    renderConfluenceGrid(pagesData);
  } else if (type === 'github') {
    title.textContent = 'GitHub Commits';
    const authors = [...new Set(commitsData.map(c => c.author_name).filter(Boolean))].sort();
    authors.forEach(a => {
      filter.innerHTML += `<option value="${esc(a)}">${esc(a)}</option>`;
    });
    renderCommitsTable(commitsData);
  }

  section.classList.add('open');
  setTimeout(() => section.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

function hideSection() {
  document.getElementById('igDetailSection').classList.remove('open');
  document.querySelectorAll('.ig-card').forEach(c => c.classList.remove('active'));
  currentSection = null;
}

// ── Setup Search & Filter ───────────────────────────────────
function setupSearch() {
  const search = document.getElementById('igSearch');
  const filter = document.getElementById('igFilter');

  const doFilter = () => {
    if (!currentSection) return;
    const q = search.value.toLowerCase().trim();
    const f = filter.value;

    if (currentSection === 'jira') {
      let filtered = ticketsData;
      if (f !== 'all') filtered = filtered.filter(t => t.status === f);
      if (q) filtered = filtered.filter(t =>
        (t.issue_key || '').toLowerCase().includes(q) ||
        (t.summary || '').toLowerCase().includes(q) ||
        (t.assignee || '').toLowerCase().includes(q)
      );
      renderJiraTable(filtered);
    } else if (currentSection === 'confluence') {
      let filtered = pagesData;
      if (f !== 'all') filtered = filtered.filter(p => p.space === f);
      if (q) filtered = filtered.filter(p =>
        (p.title || '').toLowerCase().includes(q) ||
        (p.author || '').toLowerCase().includes(q) ||
        (p.labels || []).some(l => l.toLowerCase().includes(q))
      );
      renderConfluenceGrid(filtered);
    } else if (currentSection === 'github') {
      let filtered = commitsData;
      if (f !== 'all') filtered = filtered.filter(c => c.author_name === f);
      if (q) filtered = filtered.filter(c =>
        (c.sha || '').toLowerCase().includes(q) ||
        (c.message || '').toLowerCase().includes(q) ||
        (c.author_name || '').toLowerCase().includes(q)
      );
      renderCommitsTable(filtered);
    }
  };

  search.addEventListener('input', doFilter);
  filter.addEventListener('change', doFilter);
}

// ── Render Jira Tickets Table ───────────────────────────────
function renderJiraTable(tickets) {
  const body = document.getElementById('igDetailBody');
  if (!tickets.length) {
    body.innerHTML = '<div class="ig-empty">No tickets found</div>';
    return;
  }
  body.innerHTML = `
    <table class="ig-table">
      <thead>
        <tr>
          <th>Key</th>
          <th>Type</th>
          <th>Summary</th>
          <th>Status</th>
          <th>Priority</th>
          <th>Assignee</th>
          <th>Story Pts</th>
          <th>Updated</th>
        </tr>
      </thead>
      <tbody>
        ${tickets.map(t => `
          <tr>
            <td class="cell-key">${esc(t.issue_key)}</td>
            <td class="cell-meta">${esc(t.issue_type)}</td>
            <td class="cell-summary" title="${esc(t.summary)}">${esc(t.summary)}</td>
            <td>${statusBadge(t.status)}</td>
            <td>${priorityBadge(t.priority)}</td>
            <td class="cell-meta">${esc(t.assignee || '—')}</td>
            <td class="cell-meta" style="text-align:center">${t.story_points ?? '—'}</td>
            <td class="cell-meta">${fmtDate(t.updated_date)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// ── Render Confluence Pages Grid ────────────────────────────
function renderConfluenceGrid(pages) {
  const body = document.getElementById('igDetailBody');
  if (!pages.length) {
    body.innerHTML = '<div class="ig-empty">No pages found</div>';
    return;
  }
  body.innerHTML = `
    <div class="ig-page-grid">
      ${pages.map(p => `
        <div class="ig-page-card">
          <div class="ig-page-card-title">${esc(p.title)}</div>
          <div class="ig-page-card-meta">
            <span>Space: ${esc(p.space || '—')}</span>
            <span>Author: ${esc(p.author || '—')}</span>
            <span>v${p.version || 1}</span>
            <span>${fmtDate(p.page_updated_date)}</span>
          </div>
          ${(p.labels && p.labels.length) ? `
            <div class="ig-page-labels">
              ${p.labels.map(l => `<span class="ig-page-label">${esc(l)}</span>`).join('')}
            </div>
          ` : ''}
        </div>
      `).join('')}
    </div>
  `;
}

// ── Render Commits Table ────────────────────────────────────
function renderCommitsTable(commits) {
  const body = document.getElementById('igDetailBody');
  if (!commits.length) {
    body.innerHTML = '<div class="ig-empty">No commits found</div>';
    return;
  }
  body.innerHTML = `
    <table class="ig-table">
      <thead>
        <tr>
          <th>SHA</th>
          <th>Message</th>
          <th>Author</th>
          <th>Files</th>
          <th>Changes</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        ${commits.map(c => {
          const adds = (c.files || []).reduce((s, f) => s + (f.additions || 0), 0);
          const dels = (c.files || []).reduce((s, f) => s + (f.deletions || 0), 0);
          return `
            <tr>
              <td><span class="ig-commit-sha">${esc((c.sha || '').substring(0, 7))}</span></td>
              <td class="ig-commit-msg" title="${esc(c.message)}">${esc(truncate(c.message, 60))}</td>
              <td class="cell-meta">${esc(c.author_name)}</td>
              <td class="ig-commit-files">${(c.files || []).length} file${(c.files || []).length !== 1 ? 's' : ''}</td>
              <td class="cell-meta">
                <span class="ig-commit-additions">+${adds}</span>
                <span class="ig-commit-deletions">-${dels}</span>
              </td>
              <td class="cell-meta">${fmtDate(c.commit_date)}</td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
}

// ── Helpers ─────────────────────────────────────────────────
function statusBadge(status) {
  if (!status) return '<span class="ig-badge todo">—</span>';
  const s = status.toLowerCase();
  let cls = 'todo';
  if (['done','closed','resolved','complete','completed'].includes(s)) cls = 'done';
  else if (['in progress','in development'].includes(s)) cls = 'in-progress';
  else if (['blocked','impediment'].includes(s)) cls = 'blocked';
  else if (['in review','review','code review'].includes(s)) cls = 'review';
  return `<span class="ig-badge ${cls}">${esc(status)}</span>`;
}

function priorityBadge(priority) {
  if (!priority) return '<span class="cell-meta">—</span>';
  const p = priority.toLowerCase();
  return `<span class="ig-priority ${p}"><span class="ig-priority-dot"></span>${esc(priority)}</span>`;
}

function fmtDate(d) {
  if (!d) return '—';
  try {
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch { return '—'; }
}

function truncate(s, n) {
  if (!s) return '';
  return s.length > n ? s.substring(0, n) + '...' : s;
}

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = String(s);
  return d.innerHTML;
}

// Make functions globally accessible for onclick handlers
window.showSection = showSection;
window.hideSection = hideSection;
