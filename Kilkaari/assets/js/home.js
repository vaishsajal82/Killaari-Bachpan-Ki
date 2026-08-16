/* ==========================================================================
   home.js — makes the homepage reflect what's actually in the admin portal
   instead of hardcoded content: program photos/descriptions, student
   stories, and testimonials. If the API is unreachable or a section has
   nothing published yet, the static markup already in index.html is left
   untouched as a fallback — the page never breaks or goes blank.
   ========================================================================== */

(function () {
  if (!window.KilkaariAPI) return;

  function escapeHtml(str) {
    // Must escape quotes too, not just &/</>  — these values get
    // interpolated into HTML *attributes* (style=, src=, href=,
    // aria-label=) below, and an admin-entered URL containing a stray "
    // could otherwise break out of the attribute and inject arbitrary
    // markup/event handlers (stored XSS). A DOM textContent→innerHTML
    // round-trip does NOT escape quotes, so it's not safe for this use —
    // use the same explicit regex-based escaper as events.js/gallery.js.
    return String(str || '').replace(/[&<>"']/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  // HTML-escaping alone does not stop a "javascript:..." URL from running
  // when clicked — see the matching helper + comment in events.js. Applied
  // here to story_url since it's a clickable link, not an <img>.
  function safeHref(url) {
    if (!url) return '';
    try {
      const parsed = new URL(url, window.location.href);
      return (parsed.protocol === 'http:' || parsed.protocol === 'https:') ? url : '';
    } catch (_) {
      return '';
    }
  }

  // Marks freshly-injected .reveal elements visible immediately, since
  // animation.js's IntersectionObserver only watches elements that existed
  // at initial page load and won't pick up anything added after the fact.
  function markRevealed(container) {
    container.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-visible'));
  }

  // --- Programs ("What We Do"): sync photo AND description for any card
  // whose title matches a published program in the admin portal. Titles
  // stay fixed in the HTML (they're the match key / the section's core
  // categories) — only the photo and body text update live. ---
  async function syncPrograms() {
    const grid = document.querySelector('[data-programs-grid]');
    if (!grid) return;

    let programs;
    try {
      programs = await window.KilkaariAPI.getPrograms();
    } catch (err) {
      console.warn('Programs: could not load live data, keeping static cards:', err.message);
      return;
    }
    if (!Array.isArray(programs) || !programs.length) return;

    grid.querySelectorAll('[data-program-title]').forEach((card) => {
      const title = card.getAttribute('data-program-title').trim().toLowerCase();
      const match = programs.find(
        (p) => p.is_published !== false && p.title && p.title.trim().toLowerCase() === title
      );
      if (!match) return;

      if (match.image_url) {
        const frame = card.querySelector('.photo-frame');
        if (frame) {
          frame.classList.add('has-photo');
          frame.style.backgroundImage = `url('${match.image_url}')`;
        }
      }
      if (match.description) {
        const p = card.querySelector('.program-card__body p');
        if (p) p.textContent = match.description;
      }
    });
  }

  // --- Our Stars: replace the static 4 student cards with whatever's
  // actually published in the admin portal (any number of them). ---
  async function syncStars() {
    const grid = document.querySelector('[data-stars-grid]');
    if (!grid) return;

    let stories;
    try {
      stories = await window.KilkaariAPI.getStudentStories();
    } catch (err) {
      console.warn('Student stories: could not load live data, keeping static cards:', err.message);
      return;
    }
    const published = (Array.isArray(stories) ? stories : []).filter((s) => s.is_published !== false && s.name);
    if (!published.length) return; // nothing published yet — keep the static examples rather than show an empty section

    grid.innerHTML = published
      .map((s) => {
        const hasPhoto = !!s.image_url;
        const frameStyle = hasPhoto ? ` style="background-image:url('${escapeHtml(s.image_url)}');"` : '';
        const frameClass = hasPhoto ? 'photo-frame has-photo' : 'photo-frame tone-blue';
        const link = s.story_url
          ? `<a href="${escapeHtml(safeHref(s.story_url))}" target="_blank" rel="noopener" class="program-card__link">See My Story <i class="fa-solid fa-arrow-up-right-from-square"></i></a>`
          : '';
        return `
          <article class="program-card card reveal">
            <div class="${frameClass}" role="img" aria-label="${escapeHtml(s.name)}, a Kilkaari student"${frameStyle}></div>
            <div class="program-card__body text-center">
              <h3>${escapeHtml(s.name)}</h3>
              ${link}
            </div>
          </article>`;
      })
      .join('');

    markRevealed(grid);
  }

  // --- Testimonials: replace the 3 static quotes with published
  // testimonials from the admin portal, then rebuild the slider so the
  // dots/autoplay match the new (possibly different) slide count. ---
  async function syncTestimonials() {
    const track = document.querySelector('.testimonial-track');
    if (!track) return;

    let testimonials;
    try {
      testimonials = await window.KilkaariAPI.getTestimonials();
    } catch (err) {
      console.warn('Testimonials: could not load live data, keeping static quotes:', err.message);
      return;
    }
    const published = (Array.isArray(testimonials) ? testimonials : []).filter(
      (t) => t.is_published !== false && t.quote && t.name
    );
    if (!published.length) return; // keep static examples rather than show an empty slider

    const initials = (name) =>
      name.trim().split(/\s+/).slice(0, 2).map((w) => w[0]?.toUpperCase() || '').join('');

    track.innerHTML = published
      .map((t) => {
        const avatarInner = t.avatar_url
          ? `<img src="${escapeHtml(t.avatar_url)}" alt="${escapeHtml(t.name)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">`
          : escapeHtml(initials(t.name));
        return `
          <div class="testimonial-card card">
            <p>"${escapeHtml(t.quote)}"</p>
            <div class="who">
              <div class="avatar">${avatarInner}</div>
              <div><strong>${escapeHtml(t.name)}</strong>${t.role ? `<span>${escapeHtml(t.role)}</span>` : ''}</div>
            </div>
          </div>`;
      })
      .join('');

    if (window.KilkaariTestimonials) window.KilkaariTestimonials.init();
  }

  document.addEventListener('DOMContentLoaded', () => {
    syncPrograms();
    syncStars();
    syncTestimonials();
  });
})();
