/* ==========================================================================
   main.js — site-wide behavior: newsletter form, footer year, smooth anchor
   scrolling. Section-specific behavior lives in its own file
   (navbar.js, hero.js, counter.js, gallery.js, faq.js, testimonials.js,
   animation.js) and is loaded alongside this file.
   ========================================================================== */

(function () {
  // Footer copyright year
  const yearEl = document.querySelector('[data-current-year]');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Newsletter form — calls the backend; shows the real error inline if it
  // fails, so problems are visible without opening devtools
  const newsletterForm = document.querySelector('.newsletter-form');
  if (newsletterForm) {
    let statusEl = newsletterForm.querySelector('[data-newsletter-status]');
    if (!statusEl) {
      statusEl = document.createElement('p');
      statusEl.setAttribute('data-newsletter-status', '');
      statusEl.style.cssText = 'width:100%;margin:.6rem 0 0;font-size:.8rem;';
      newsletterForm.after(statusEl);
    }

    newsletterForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const input = newsletterForm.querySelector('input[type="email"]');
      const button = newsletterForm.querySelector('button');
      if (!input || !input.value) return;

      const original = button.textContent;
      button.disabled = true;
      button.textContent = '...';
      statusEl.textContent = '';

      try {
        if (!window.KilkaariAPI) {
          throw new Error('api.js did not load — check the <script> tags in this page.');
        }
        await window.KilkaariAPI.subscribeNewsletter(input.value);
        button.textContent = 'Subscribed';
        statusEl.textContent = '';
        input.value = '';
      } catch (err) {
        console.error('Newsletter subscribe failed:', err);
        button.textContent = 'Try again';
        statusEl.textContent = `Couldn't reach the backend: ${err.message}`;
        statusEl.style.color = '#ffb4b4';
      } finally {
        button.disabled = false;
        setTimeout(() => (button.textContent = original), 3500);
      }
    });
  }

  // Generic form submit handler for pages that add [data-demo-form] +
  // [data-endpoint="/api/..."] to a <form> (contact, volunteer, donate).
  // Falls back to a local success message if the API isn't reachable.
  document.querySelectorAll('[data-demo-form]').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const note = form.querySelector('[data-form-success]');
      const endpoint = form.getAttribute('data-endpoint');

      try {
        if (endpoint && window.KilkaariAPI) {
          const formData = new FormData(form);
          const payload = Object.fromEntries(formData.entries());
          const res = await fetch(`${window.KilkaariAPI.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          if (!res.ok) throw new Error(`Request failed (${res.status})`);
        }
        if (note) {
          note.hidden = false;
          note.textContent = note.textContent || 'Thank you — we received your submission.';
          note.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        form.reset();
      } catch (err) {
        console.error('Form submit failed:', err);
        if (note) {
          note.hidden = false;
          note.textContent = "Something went wrong — please try again, or reach us directly.";
          note.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    });
  });
})();
