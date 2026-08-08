/* ==========================================================================
   Kilkaari Admin Portal — admin.js
   Single-file app logic: auth, page switching, dashboard, and a generic
   CRUD system driven by CONTENT_TYPES config (used for programs, events,
   campaigns, gallery, testimonials, centers, student-stories).
   ========================================================================== */

const API_BASE_URL = window.KILKAARI_API_BASE_URL || 'https://killaari-bachpan-ki.onrender.com';
const TOKEN_KEY = 'kilkaari_admin_token';

// ---------------------------------------------------------------------------
// Low-level API helper
// ---------------------------------------------------------------------------
async function api(path, { method = 'GET', body, auth = true, form = false } = {}) {
  const headers = {};
  if (!form) headers['Content-Type'] = 'application/json';
  if (auth) {
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: form ? body : body ? JSON.stringify(body) : undefined,
    });
  } catch (_networkErr) {
    // fetch() itself failed — the request never reached the server at all
    // (backend not deployed/asleep/down, or blocked by CORS). This is the
    // single place every admin action goes through, so fixing the message
    // here (rather than in each caller) fixes it everywhere at once —
    // login, saving, deleting, uploading, all of it.
    throw new Error(`Can't reach the server at ${API_BASE_URL}. It may be waking up (wait ~30s and retry), not deployed yet, or down — check the banner at the top of the page.`);
  }

  if (res.status === 401 && auth) {
    logout();
    throw new Error('Session expired — please log in again.');
  }

  let data = null;
  try { data = await res.json(); } catch (_) {}

  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || `Request failed (${res.status})`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

// ---------------------------------------------------------------------------
// Backend connectivity check
// ---------------------------------------------------------------------------
// A plain fetch() that can't reach the server at all (backend not deployed,
// asleep, down, or blocked by CORS) throws a raw "Failed to fetch" TypeError
// that's meaningless to a non-technical admin. This pings the lightweight
// /api/health route on load (and lets the admin retry) so that kind of
// failure surfaces as a clear banner instead of only showing up later, deep
// inside a specific form (e.g. the image upload button).
async function checkBackendReachable() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, { method: 'GET' });
    return res.ok;
  } catch (_) {
    return false;
  }
}

async function refreshConnectionBanner() {
  const banner = document.getElementById('connection-banner');
  const text = document.getElementById('connection-banner-text');
  if (!banner) return;
  const ok = await checkBackendReachable();
  if (ok) {
    banner.hidden = true;
  } else {
    text.textContent = `Can't reach the backend server at ${API_BASE_URL} — it may not be deployed, may be waking up (this can take up to a minute on a free-tier host), or may be down. Uploads, saving, and editing won't work until this is resolved.`;
    banner.hidden = false;
  }
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function toast(message, isError = false) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.className = isError ? 'error show' : 'show';
  setTimeout(() => (el.className = ''), 3200);
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
function logout() {
  sessionStorage.removeItem(TOKEN_KEY);
  document.querySelector('.app-shell').classList.remove('is-active');
  document.querySelector('.login-screen').style.display = 'flex';
}

async function tryRestoreSession() {
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (!token) return false;
  try {
    const me = await api('/api/auth/me');
    if (me.role !== 'admin') { toast('This account is not an admin.', true); logout(); return false; }
    enterApp(me);
    return true;
  } catch (_) {
    return false;
  }
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const errorEl = document.getElementById('login-error');
  errorEl.style.display = 'none';

  try {
    const result = await api('/api/auth/login', { method: 'POST', body: { email, password }, auth: false });
    if (result.user.role !== 'admin') throw new Error('This account is not an admin.');
    sessionStorage.setItem(TOKEN_KEY, result.access_token);
    enterApp(result.user);
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = 'block';
  }
});

document.getElementById('logout-btn').addEventListener('click', logout);

function enterApp(user) {
  document.querySelector('.login-screen').style.display = 'none';
  document.querySelector('.app-shell').classList.add('is-active');
  document.getElementById('current-user').textContent = user.full_name || user.email;
  loadDashboard();
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
const PAGE_LOADERS = {
  dashboard: loadDashboard,
  donations: loadDonations,
  volunteers: loadVolunteers,
  messages: loadMessages,
  users: loadUsers,
  programs: () => loadContent('programs'),
  events: () => loadContent('events'),
  campaigns: () => loadContent('campaigns'),
  gallery: () => loadContent('gallery'),
  testimonials: () => loadContent('testimonials'),
  centers: () => loadContent('centers'),
  'student-stories': () => loadContent('student-stories'),
};

document.querySelectorAll('.nav-item').forEach((btn) => {
  btn.addEventListener('click', () => {
    const target = btn.getAttribute('data-page');
    document.querySelectorAll('.nav-item').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.page').forEach((p) => p.classList.remove('is-active'));
    document.getElementById(`page-${target}`).classList.add('is-active');
    document.querySelector('.sidebar').classList.remove('is-open');
    const loader = PAGE_LOADERS[target];
    if (loader) loader();
  });
});

document.getElementById('hamburger').addEventListener('click', () => {
  document.querySelector('.sidebar').classList.toggle('is-open');
});

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------
async function loadDashboard() {
  const grid = document.getElementById('stat-grid');
  grid.innerHTML = '<p style="color:var(--color-ink-soft);">Loading…</p>';
  try {
    const d = await api('/api/admin/dashboard');
    grid.innerHTML = `
      <div class="stat-card"><div class="num">₹${d.total_donations_amount.toLocaleString('en-IN')}</div><div class="label">Total Donations Raised</div></div>
      <div class="stat-card"><div class="num">${d.successful_donations_count}/${d.total_donations_count}</div><div class="label">Successful / Total Donations</div></div>
      <div class="stat-card"><div class="num">${d.pending_volunteer_applications}</div><div class="label">Pending Volunteer Applications</div></div>
      <div class="stat-card"><div class="num">${d.unread_contact_messages}</div><div class="label">Unread Messages</div></div>
      <div class="stat-card"><div class="num">${d.newsletter_subscribers}</div><div class="label">Newsletter Subscribers</div></div>
      <div class="stat-card"><div class="num">${d.active_campaigns}</div><div class="label">Active Campaigns</div></div>
    `;
    updateSidebarBadges(d);
  } catch (err) {
    grid.innerHTML = `<p style="color:var(--color-danger);">Couldn't load dashboard: ${err.message}</p>`;
  }
}

function updateSidebarBadges(d) {
  setBadge('nav-volunteers-badge', d.pending_volunteer_applications);
  setBadge('nav-messages-badge', d.unread_contact_messages);
}
function setBadge(id, count) {
  const el = document.getElementById(id);
  if (!el) return;
  if (count > 0) { el.textContent = count; el.style.display = 'inline-block'; }
  else { el.style.display = 'none'; }
}

// ---------------------------------------------------------------------------
// Donations (read-only)
// ---------------------------------------------------------------------------
async function loadDonations() {
  const tbody = document.querySelector('#donations-table tbody');
  tbody.innerHTML = `<tr class="empty-row"><td colspan="6">Loading…</td></tr>`;
  try {
    const rows = await api('/api/admin/donations');
    if (!rows.length) { tbody.innerHTML = `<tr class="empty-row"><td colspan="6">No donations yet.</td></tr>`; return; }
    tbody.innerHTML = rows.map((r) => `
      <tr>
        <td>${r.donor_name}<br><span style="color:var(--color-ink-soft);font-size:.78rem;">${r.donor_email}</span></td>
        <td>₹${r.amount.toLocaleString('en-IN')}</td>
        <td>${r.donation_type === 'monthly_child_sponsorship' ? 'Monthly Sponsorship' : 'One-Time'}</td>
        <td><span class="pill pill-${r.status}">${r.status}</span></td>
        <td>${r.payment_provider || '—'}</td>
        <td>${new Date(r.created_at).toLocaleDateString('en-IN')}</td>
      </tr>`).join('');
  } catch (err) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="6" style="color:var(--color-danger);">${err.message}</td></tr>`;
  }
}

// ---------------------------------------------------------------------------
// Volunteer applications
// ---------------------------------------------------------------------------
async function loadVolunteers() {
  const tbody = document.querySelector('#volunteers-table tbody');
  tbody.innerHTML = `<tr class="empty-row"><td colspan="6">Loading…</td></tr>`;
  try {
    const rows = await api('/api/admin/volunteer-applications');
    if (!rows.length) { tbody.innerHTML = `<tr class="empty-row"><td colspan="6">No applications yet.</td></tr>`; return; }
    tbody.innerHTML = rows.map((r) => `
      <tr>
        <td>${r.full_name}<br><span style="color:var(--color-ink-soft);font-size:.78rem;">${r.email} · ${r.phone}</span></td>
        <td>${r.city || '—'}</td>
        <td>${r.area_of_interest || '—'}</td>
        <td>${r.availability || '—'}</td>
        <td>
          <select class="status-select" data-app-id="${r.id}">
            ${['new','reviewed','accepted','rejected'].map((s) => `<option value="${s}" ${s === r.status ? 'selected' : ''}>${s}</option>`).join('')}
          </select>
        </td>
        <td>${new Date(r.created_at).toLocaleDateString('en-IN')}</td>
      </tr>`).join('');

    tbody.querySelectorAll('.status-select').forEach((select) => {
      select.addEventListener('change', async () => {
        try {
          await api(`/api/admin/volunteer-applications/${select.dataset.appId}`, {
            method: 'PATCH',
            body: { status: select.value },
          });
          toast('Application status updated.');
          loadDashboard();
        } catch (err) {
          toast(err.message, true);
        }
      });
    });
  } catch (err) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="6" style="color:var(--color-danger);">${err.message}</td></tr>`;
  }
}

// ---------------------------------------------------------------------------
// Contact messages
// ---------------------------------------------------------------------------
async function loadMessages() {
  const tbody = document.querySelector('#messages-table tbody');
  tbody.innerHTML = `<tr class="empty-row"><td colspan="5">Loading…</td></tr>`;
  try {
    const rows = await api('/api/admin/contact-messages');
    if (!rows.length) { tbody.innerHTML = `<tr class="empty-row"><td colspan="5">No messages yet.</td></tr>`; return; }
    tbody.innerHTML = rows.map((r) => `
      <tr>
        <td>${r.full_name}<br><span style="color:var(--color-ink-soft);font-size:.78rem;">${r.email}${r.phone ? ' · ' + r.phone : ''}</span></td>
        <td style="max-width:320px;">${r.comment}</td>
        <td><span class="pill pill-${r.is_read}">${r.is_read ? 'Read' : 'Unread'}</span></td>
        <td>${new Date(r.created_at).toLocaleDateString('en-IN')}</td>
        <td>${r.is_read ? '' : `<button class="btn btn-outline btn-sm" data-mark-read="${r.id}">Mark Read</button>`}</td>
      </tr>`).join('');

    tbody.querySelectorAll('[data-mark-read]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        try {
          await api(`/api/admin/contact-messages/${btn.dataset.markRead}/mark-read`, { method: 'PATCH' });
          toast('Marked as read.');
          loadMessages();
          loadDashboard();
        } catch (err) {
          toast(err.message, true);
        }
      });
    });
  } catch (err) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="5" style="color:var(--color-danger);">${err.message}</td></tr>`;
  }
}

// ---------------------------------------------------------------------------
// Users
// ---------------------------------------------------------------------------
async function loadUsers() {
  const tbody = document.querySelector('#users-table tbody');
  tbody.innerHTML = `<tr class="empty-row"><td colspan="5">Loading…</td></tr>`;
  try {
    const rows = await api('/api/admin/users');
    if (!rows.length) { tbody.innerHTML = `<tr class="empty-row"><td colspan="5">No users yet.</td></tr>`; return; }
    tbody.innerHTML = rows.map((r) => `
      <tr>
        <td>${r.full_name}</td>
        <td>${r.email}</td>
        <td><span class="pill pill-${r.role === 'admin' ? 'accepted' : 'reviewed'}">${r.role}</span></td>
        <td><span class="pill pill-${r.is_active}">${r.is_active ? 'Active' : 'Deactivated'}</span></td>
        <td>${r.is_active && r.role !== 'admin' ? `<button class="btn btn-danger btn-sm" data-deactivate="${r.id}">Deactivate</button>` : ''}</td>
      </tr>`).join('');

    tbody.querySelectorAll('[data-deactivate]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        if (!confirm('Deactivate this user?')) return;
        try {
          await api(`/api/admin/users/${btn.dataset.deactivate}/deactivate`, { method: 'PATCH' });
          toast('User deactivated.');
          loadUsers();
        } catch (err) {
          toast(err.message, true);
        }
      });
    });
  } catch (err) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="5" style="color:var(--color-danger);">${err.message}</td></tr>`;
  }
}

// ---------------------------------------------------------------------------
// Generic content CRUD (programs, events, campaigns, gallery, testimonials,
// centers, student-stories) — driven by CONTENT_TYPES config below.
// ---------------------------------------------------------------------------
const CONTENT_TYPES = {
  programs: {
    endpoint: '/api/programs',
    label: 'Program',
    columns: [
      { key: 'title', label: 'Title' },
      { key: 'summary', label: 'Summary' },
      { key: 'display_order', label: 'Order' },
      { key: 'is_published', label: 'Published', bool: true },
    ],
    fields: [
      { key: 'title', label: 'Title', type: 'text', required: true },
      { key: 'slug', label: 'Slug', type: 'text', required: true },
      { key: 'summary', label: 'Summary', type: 'text', required: true },
      { key: 'description', label: 'Description', type: 'textarea' },
      { key: 'icon', label: 'Icon (Font Awesome class)', type: 'text' },
      { key: 'image_url', label: 'Image URL', type: 'image-url' },
      { key: 'display_order', label: 'Display Order', type: 'number', default: 0 },
      { key: 'is_published', label: 'Published', type: 'checkbox', default: true },
    ],
  },
  events: {
    endpoint: '/api/events',
    label: 'Event',
    statusActions: true, // adds Mark Done / Postpone / Reopen buttons to each row
    columns: [
      { key: 'title', label: 'Title' },
      { key: 'location', label: 'Location' },
      { key: 'event_date', label: 'Date', date: true },
      { key: 'status', label: 'Status', pill: true },
      { key: 'is_published', label: 'Published', bool: true },
    ],
    fields: [
      { key: 'title', label: 'Title', type: 'text', required: true },
      { key: 'description', label: 'Description', type: 'textarea' },
      { key: 'location', label: 'Location', type: 'text' },
      { key: 'event_date', label: 'Date & Time', type: 'datetime-local', required: true },
      { key: 'image_url', label: 'Image URL', type: 'image-url' },
      { key: 'registration_url', label: 'Registration URL', type: 'text' },
      {
        key: 'status', label: 'Status', type: 'select', default: 'upcoming',
        options: [
          { value: 'upcoming', label: 'Upcoming' },
          { value: 'completed', label: 'Completed / Done' },
          { value: 'postponed', label: 'Postponed' },
        ],
      },
      { key: 'is_published', label: 'Published', type: 'checkbox', default: true },
    ],
  },
  campaigns: {
    endpoint: '/api/campaigns',
    label: 'Campaign',
    columns: [
      { key: 'title', label: 'Title' },
      { key: 'goal_amount', label: 'Goal (₹)' },
      { key: 'raised_amount', label: 'Raised (₹)' },
      { key: 'is_active', label: 'Active', bool: true },
    ],
    fields: [
      { key: 'title', label: 'Title', type: 'text', required: true },
      { key: 'slug', label: 'Slug', type: 'text', required: true },
      { key: 'description', label: 'Description', type: 'textarea' },
      { key: 'image_url', label: 'Image URL', type: 'image-url' },
      { key: 'goal_amount', label: 'Goal Amount (₹)', type: 'number', required: true },
      { key: 'is_active', label: 'Active', type: 'checkbox', default: true },
    ],
  },
  gallery: {
    endpoint: '/api/gallery',
    label: 'Gallery Item',
    columns: [
      { key: 'title', label: 'Title' },
      { key: 'category', label: 'Category' },
      { key: 'display_order', label: 'Order' },
    ],
    fields: [
      { key: 'title', label: 'Title', type: 'text' },
      { key: 'image_url', label: 'Image URL (must be a direct link ending in an image, e.g. .jpg/.png — not a Google Drive/Dropbox share link)', type: 'image-url', required: true },
      { key: 'category', label: 'Category', type: 'text' },
      { key: 'caption', label: 'Caption', type: 'text' },
      { key: 'display_order', label: 'Display Order', type: 'number', default: 0 },
    ],
  },
  testimonials: {
    endpoint: '/api/testimonials',
    label: 'Testimonial',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'role', label: 'Role' },
      { key: 'quote', label: 'Quote' },
      { key: 'is_published', label: 'Published', bool: true },
    ],
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'role', label: 'Role (e.g. Parent, Volunteer)', type: 'text' },
      { key: 'quote', label: 'Quote', type: 'textarea', required: true },
      { key: 'avatar_url', label: 'Avatar URL', type: 'image-url' },
      { key: 'is_published', label: 'Published', type: 'checkbox', default: true },
    ],
  },
  centers: {
    endpoint: '/api/centers',
    label: 'Center',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'address', label: 'Address' },
      { key: 'is_active', label: 'Active', bool: true },
    ],
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'address', label: 'Address', type: 'text', required: true },
      { key: 'map_url', label: 'Map URL', type: 'text' },
      { key: 'is_active', label: 'Active', type: 'checkbox', default: true },
    ],
  },
  'student-stories': {
    endpoint: '/api/student-stories',
    label: 'Student Story',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'story_url', label: 'Story URL' },
      { key: 'is_published', label: 'Published', bool: true },
    ],
    fields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'story_url', label: 'Story URL', type: 'text' },
      { key: 'image_url', label: 'Image URL', type: 'image-url' },
      { key: 'is_published', label: 'Published', type: 'checkbox', default: true },
    ],
  },
};

const contentCache = {}; // type -> array of rows, so edit-modal can look up current values

async function loadContent(type) {
  const config = CONTENT_TYPES[type];
  const tbody = document.querySelector(`#content-${type}-table tbody`);
  tbody.innerHTML = `<tr class="empty-row"><td colspan="${config.columns.length + 1}">Loading…</td></tr>`;
  try {
    const rows = await api(config.endpoint, { auth: false });
    contentCache[type] = rows;
    if (!rows.length) {
      tbody.innerHTML = `<tr class="empty-row"><td colspan="${config.columns.length + 1}">No ${config.label.toLowerCase()}s yet — click "Add ${config.label}" to create one.</td></tr>`;
      return;
    }
    tbody.innerHTML = rows.map((row) => `
      <tr>
        ${config.columns.map((col) => `<td>${renderCell(row, col)}</td>`).join('')}
        <td class="row-actions">
          ${renderStatusActions(type, row)}
          <button class="btn btn-outline btn-sm" data-edit="${row.id}">Edit</button>
          <button class="btn btn-danger btn-sm" data-delete="${row.id}">Delete</button>
        </td>
      </tr>`).join('');

    tbody.querySelectorAll('[data-edit]').forEach((btn) => {
      btn.addEventListener('click', () => openContentModal(type, btn.dataset.edit));
    });
    tbody.querySelectorAll('[data-delete]').forEach((btn) => {
      btn.addEventListener('click', () => deleteContentItem(type, btn.dataset.delete));
    });
    tbody.querySelectorAll('[data-set-status]').forEach((btn) => {
      btn.addEventListener('click', () => setContentStatus(type, btn.dataset.id, btn.dataset.setStatus));
    });
  } catch (err) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="${config.columns.length + 1}" style="color:var(--color-danger);">${err.message}</td></tr>`;
  }
}

function renderCell(row, col) {
  const val = row[col.key];
  if (col.bool) return `<span class="pill pill-${val}">${val ? 'Yes' : 'No'}</span>`;
  if (col.pill) return `<span class="pill pill-${val}">${STATUS_LABELS[val] || val}</span>`;
  if (col.date && val) return new Date(val).toLocaleString('en-IN');
  if (val === null || val === undefined || val === '') return '—';
  const text = String(val);
  return text.length > 60 ? text.slice(0, 60) + '…' : text;
}

const STATUS_LABELS = { upcoming: 'Upcoming', completed: 'Completed', postponed: 'Postponed' };

// For content types with `statusActions: true` (currently just events): quick
// one-click buttons so an admin doesn't have to open the edit modal just to
// mark something done or postponed. Reuses the same generic PUT endpoint.
function renderStatusActions(type, row) {
  const config = CONTENT_TYPES[type];
  if (!config.statusActions) return '';
  const buttons = [];
  if (row.status !== 'completed') {
    buttons.push(`<button class="btn btn-outline btn-sm" data-set-status="completed" data-id="${row.id}">Mark Done</button>`);
  }
  if (row.status !== 'postponed') {
    buttons.push(`<button class="btn btn-outline btn-sm" data-set-status="postponed" data-id="${row.id}">Postpone</button>`);
  }
  if (row.status !== 'upcoming') {
    buttons.push(`<button class="btn btn-outline btn-sm" data-set-status="upcoming" data-id="${row.id}">Reopen</button>`);
  }
  return buttons.join(' ');
}

async function setContentStatus(type, id, status) {
  const config = CONTENT_TYPES[type];
  try {
    await api(`${config.endpoint}/${id}`, { method: 'PUT', body: { status } });
    toast(`${config.label} marked as ${STATUS_LABELS[status] || status}.`);
    loadContent(type);
  } catch (err) {
    toast(err.message, true);
  }
}

async function deleteContentItem(type, id) {
  const config = CONTENT_TYPES[type];
  if (!confirm(`Delete this ${config.label.toLowerCase()}? This can't be undone.`)) return;
  try {
    await api(`${config.endpoint}/${id}`, { method: 'DELETE' });
    toast(`${config.label} deleted.`);
    loadContent(type);
  } catch (err) {
    toast(err.message, true);
  }
}

// Add-content buttons
document.querySelectorAll('[data-add-content]').forEach((btn) => {
  btn.addEventListener('click', () => openContentModal(btn.dataset.addContent, null));
});

function openContentModal(type, id) {
  const config = CONTENT_TYPES[type];
  const existing = id ? (contentCache[type] || []).find((r) => r.id === id) : null;

  const backdrop = document.getElementById('modal-backdrop');
  const modal = document.getElementById('modal');
  modal.innerHTML = `
    <button class="modal-close" id="modal-close-btn">&times;</button>
    <h3>${existing ? 'Edit' : 'Add'} ${config.label}</h3>
    <form id="content-form">
      ${config.fields.map((f) => renderField(f, existing)).join('')}
      <div class="modal-actions">
        <button type="submit" class="btn btn-primary">${existing ? 'Save Changes' : 'Create'}</button>
        <button type="button" class="btn btn-outline" id="modal-cancel-btn">Cancel</button>
      </div>
    </form>
  `;
  backdrop.classList.add('is-open');

  config.fields.filter((f) => f.type === 'image-url').forEach((f) => {
    wireImagePreview(`field-${f.key}`, `preview-${f.key}`);
    wireImageUpload(f.key);
  });

  document.getElementById('modal-close-btn').addEventListener('click', closeModal);
  document.getElementById('modal-cancel-btn').addEventListener('click', closeModal);
  backdrop.addEventListener('click', (e) => { if (e.target === backdrop) closeModal(); });

  document.getElementById('content-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {};
    config.fields.forEach((f) => {
      const el = document.getElementById(`field-${f.key}`);
      if (f.type === 'checkbox') payload[f.key] = el.checked;
      else if (f.type === 'number') payload[f.key] = el.value === '' ? null : parseFloat(el.value);
      else if (f.type === 'datetime-local') payload[f.key] = el.value ? `${el.value}:00` : null;
      else payload[f.key] = el.value || null;
    });

    try {
      if (existing) {
        await api(`${config.endpoint}/${existing.id}`, { method: 'PUT', body: payload });
        toast(`${config.label} updated.`);
      } else {
        await api(config.endpoint, { method: 'POST', body: payload });
        toast(`${config.label} created.`);
      }
      closeModal();
      loadContent(type);
    } catch (err) {
      toast(err.message, true);
    }
  });
}

// Formats a Date as the local (not UTC) "YYYY-MM-DDTHH:mm" string a
// datetime-local input expects. Using Date.toISOString() here would be a
// bug: it normalizes to UTC, so re-opening an event for editing would show
// (and, if saved without changes, silently rewrite) a time shifted by the
// browser's UTC offset — e.g. a 9:00 AM IST event would show as 3:30 AM.
function toDatetimeLocalValue(dateInput) {
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function renderField(f, existing) {
  const value = existing ? existing[f.key] : f.default;
  if (f.type === 'checkbox') {
    return `
      <div class="form-group">
        <label class="form-label"><input type="checkbox" id="field-${f.key}" ${value ? 'checked' : ''}> ${f.label}</label>
      </div>`;
  }
  if (f.type === 'textarea') {
    return `
      <div class="form-group">
        <label class="form-label" for="field-${f.key}">${f.label}</label>
        <textarea class="form-control" id="field-${f.key}" ${f.required ? 'required' : ''}>${value || ''}</textarea>
      </div>`;
  }
  if (f.type === 'datetime-local') {
    const dtValue = value ? toDatetimeLocalValue(value) : '';
    return `
      <div class="form-group">
        <label class="form-label" for="field-${f.key}">${f.label}</label>
        <input class="form-control" type="datetime-local" id="field-${f.key}" value="${dtValue}" ${f.required ? 'required' : ''}>
      </div>`;
  }
  if (f.type === 'select') {
    return `
      <div class="form-group">
        <label class="form-label" for="field-${f.key}">${f.label}</label>
        <select class="form-control" id="field-${f.key}" ${f.required ? 'required' : ''}>
          ${f.options.map((o) => `<option value="${o.value}" ${o.value === (value ?? f.default) ? 'selected' : ''}>${o.label}</option>`).join('')}
        </select>
      </div>`;
  }
  if (f.type === 'image-url') {
    return `
      <div class="form-group">
        <label class="form-label" for="field-${f.key}">${f.label}</label>
        <input class="form-control" type="text" id="field-${f.key}" value="${value ?? ''}" placeholder="https://..." ${f.required ? 'required' : ''}>
        <div class="image-upload-row" style="margin-top:.5rem; display:flex; align-items:center; gap:.6rem;">
          <label class="btn btn-outline btn-sm" style="cursor:pointer;">
            <i class="fa-solid fa-upload"></i> Upload from computer
            <input type="file" id="upload-${f.key}" accept="image/png,image/jpeg,image/gif,image/webp" style="display:none;">
          </label>
          <span class="upload-status" id="upload-status-${f.key}" style="font-size:.82rem; color:var(--color-text-muted,#777);"></span>
        </div>
        <div class="image-url-preview" id="preview-${f.key}" style="margin-top:.6rem;"></div>
      </div>`;
  }
  return `
    <div class="form-group">
      <label class="form-label" for="field-${f.key}">${f.label}</label>
      <input class="form-control" type="${f.type}" id="field-${f.key}" value="${value ?? ''}" ${f.required ? 'required' : ''}>
    </div>`;
}

// Watches an image-url text input and shows a live thumbnail (or a clear
// error) below it, so an admin finds out *before* saving whether the URL
// they pasted is actually a direct image link — instead of finding out
// later that it's not showing up on the public gallery page.
function wireImagePreview(inputId, previewId) {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  if (!input || !preview) return;

  let debounceTimer = null;

  function checkUrl() {
    const url = input.value.trim();
    if (!url) {
      preview.innerHTML = '';
      return;
    }

    let isValidUrl = false;
    try {
      const parsed = new URL(url);
      isValidUrl = parsed.protocol === 'http:' || parsed.protocol === 'https:';
    } catch (_) {
      isValidUrl = false;
    }
    if (!isValidUrl) {
      preview.innerHTML = `<p style="color:var(--color-danger,#c0392b); font-size:.85rem;">⚠️ Not a valid URL yet.</p>`;
      return;
    }

    const shareHostPattern = /drive\.google\.com|dropbox\.com|pinterest\.(com|co)/i;
    const isDriveOk = /drive\.google\.com/i.test(url) && (/\/uc\?/.test(url) || /\/thumbnail\?/.test(url));
    if (shareHostPattern.test(url) && !isDriveOk) {
      preview.innerHTML = `<p style="color:var(--color-danger,#c0392b); font-size:.85rem;">⚠️ This looks like a share/preview link, not a direct image link — it likely won't render on the site. Use a direct-image host (Cloudinary, Imgur, S3) or a direct-download link.</p>`;
      return;
    }

    preview.innerHTML = `<p style="font-size:.85rem; color:var(--color-muted,#777);">Loading preview…</p>`;
    const img = new Image();
    img.onload = () => {
      preview.innerHTML = `
        <img src="${url}" alt="Preview" style="max-width:160px; max-height:160px; border-radius:8px; display:block; object-fit:cover;">
        <p style="font-size:.8rem; color:var(--color-success,#2e7d32); margin-top:.3rem;">✓ Image loads correctly.</p>`;
    };
    img.onerror = () => {
      preview.innerHTML = `<p style="color:var(--color-danger,#c0392b); font-size:.85rem;">⚠️ Couldn't load an image from this URL. Double-check it's a direct link to an image file, and that the host allows hotlinking.</p>`;
    };
    img.src = url;
  }

  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(checkUrl, 500);
  });
  checkUrl(); // check immediately for edit mode, where a value may already be present
}

// Wires the "Upload from computer" file input next to an image-url field:
// on file select, POSTs it to /api/uploads, drops the returned URL straight
// into the text field (which then triggers the existing preview/validation
// via its own 'input' listener), so admins don't need to already have the
// photo hosted somewhere else first.
function wireImageUpload(fieldKey) {
  const fileInput = document.getElementById(`upload-${fieldKey}`);
  const urlInput = document.getElementById(`field-${fieldKey}`);
  const status = document.getElementById(`upload-status-${fieldKey}`);
  if (!fileInput || !urlInput) return;

  fileInput.addEventListener('change', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    if (status) {
      status.textContent = 'Uploading…';
      status.style.color = 'var(--color-text-muted,#777)';
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      const data = await api('/api/uploads', { method: 'POST', body: formData, form: true });
      urlInput.value = data.url;
      urlInput.dispatchEvent(new Event('input')); // re-runs the live preview check
      if (status) {
        status.textContent = '✓ Uploaded';
        status.style.color = 'var(--color-success,#2e7d32)';
      }
    } catch (err) {
      // err.message is already a clear, actionable string here — either
      // the friendly network-failure message from api(), or a normal
      // validation/size/type error from the upload endpoint itself.
      if (status) {
        status.textContent = `⚠️ ${err.message}`;
        status.style.color = 'var(--color-danger,#c0392b)';
      }
    } finally {
      fileInput.value = '';
    }
  });
}

function closeModal() {
  document.getElementById('modal-backdrop').classList.remove('is-open');
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
tryRestoreSession();
refreshConnectionBanner();
document.getElementById('connection-banner-retry')?.addEventListener('click', refreshConnectionBanner);
