/* ==========================================================================
   events.js — fetches events from the backend and renders them into the
   Upcoming and Past Events lists, reflecting whatever status ("upcoming",
   "completed", "postponed") the admin set for each event. Falls back to the
   static placeholder markup already in events.html if the API is
   unreachable or returns nothing.
   ========================================================================== */

(function () {
  const upcomingList = document.getElementById('events-list');
  const pastList = document.getElementById('past-events-list');

  if (!upcomingList && !pastList) return;

  function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  // HTML-escaping alone does NOT stop a "javascript:alert(1)" URL from
  // executing when the link is clicked — there's nothing HTML-special
  // about that string for escapeHtml() to catch. This is defense-in-depth
  // for any registration_url saved before the backend validator existed;
  // the backend now also rejects non-http(s) schemes on save.
  function safeHref(url, fallback) {
    if (!url) return fallback;
    try {
      const parsed = new URL(url, window.location.href);
      return (parsed.protocol === 'http:' || parsed.protocol === 'https:') ? url : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function eventCard(e) {
    const d = new Date(e.event_date);
    const day = d.getDate();
    const mon = d.toLocaleString('en-US', { month: 'short' });
    const time = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    const isPast = e.status === 'completed';
    const isPostponed = e.status === 'postponed';

    const badge = isPostponed
      ? '<span class="event-status-badge is-postponed">Postponed</span>'
      : (isPast ? '<span class="event-status-badge is-completed">Completed</span>' : '');

    const cta = isPast
      ? ''
      : `<a href="${escapeHtml(safeHref(e.registration_url, 'contact.html'))}" class="btn btn-outline btn-sm event-card__cta">Register</a>`;

    return `
      <div class="event-card card reveal is-visible${isPast || isPostponed ? ' is-inactive' : ''}">
        <div class="event-card__date"><span class="day">${day}</span><span class="mon">${mon}</span></div>
        <div class="event-card__divider"></div>
        <div class="event-card__info">
          <h3>${escapeHtml(e.title)} ${badge}</h3>
          <div class="meta">
            <span><i class="fa-regular fa-clock"></i> ${time}</span>
            ${e.location ? `<span><i class="fa-solid fa-location-dot"></i> ${escapeHtml(e.location)}</span>` : ''}
          </div>
        </div>
        ${cta}
      </div>`;
  }

  async function init() {
    if (!window.KilkaariAPI) return;
    try {
      const events = await window.KilkaariAPI.getEvents();
      if (!Array.isArray(events) || !events.length) return; // keep static placeholder markup

      const sorted = events.slice().sort((a, b) => new Date(a.event_date) - new Date(b.event_date));

      // "Upcoming" section: anything not marked completed (so postponed
      // events still show there, with a badge, rather than disappearing).
      const upcoming = sorted.filter((e) => e.status !== 'completed');
      // "Past" section: anything the admin has marked done.
      const past = sorted.filter((e) => e.status === 'completed').reverse();

      if (upcomingList) {
        upcomingList.innerHTML = upcoming.length
          ? upcoming.map(eventCard).join('')
          : '<p class="events-empty">No upcoming events right now — check back soon.</p>';
      }
      if (pastList && past.length) {
        pastList.innerHTML = past.map(eventCard).join('');
      }
    } catch (err) {
      console.warn('Could not load live events, showing static list:', err.message);
    }
  }

  init();
})();
