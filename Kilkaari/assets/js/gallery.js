/* ==========================================================================
   gallery.js — fetches gallery items from the backend (falls back to the
   static placeholder markup already in gallery.html if the API is
   unreachable or empty), then wires up category filters + modal preview.
   ========================================================================== */

(function () {
  const grid = document.querySelector('[data-gallery-grid]');
  const filters = document.querySelectorAll('[data-gallery-filter]');
  const modal = document.querySelector('[data-gallery-modal]');

  if (!grid) return;

  const TONES = ['tone-blue', 'tone-gold', 'tone-dark', '']; // cycle for items with no image

  function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  function renderItems(items) {
    grid.innerHTML = items.map((item, i) => {
      const category = escapeHtml(item.category || 'events');
      const caption = escapeHtml(item.title || item.caption || '');
      const hasPhoto = !!item.image_url;
      const frameClass = hasPhoto ? 'photo-frame has-photo' : `photo-frame ${TONES[i % TONES.length]}`;
      const frameStyle = hasPhoto
        ? `background-image:url('${escapeHtml(item.image_url)}');`
        : '';
      return `
        <div class="gallery-item reveal" data-category="${category}" data-caption="${caption}" data-image="${escapeHtml(item.image_url || '')}">
          <div class="${frameClass}" style="${frameStyle}" role="img" aria-label="${caption}"></div>
        </div>`;
    }).join('');
     grid.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-visible'));
  }

  function wireUpInteractions() {
    // Category filtering
    filters.forEach((btn) => {
      btn.addEventListener('click', () => {
        filters.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        const category = btn.getAttribute('data-gallery-filter');

        grid.querySelectorAll('.gallery-item').forEach((item) => {
          const match = category === 'all' || item.getAttribute('data-category') === category;
          item.style.display = match ? '' : 'none';
        });
      });
    });

    // Modal preview
    if (modal) {
      const modalImg = modal.querySelector('[data-modal-frame]');
      const modalPhoto = modal.querySelector('[data-modal-img]');
      const modalCaption = modal.querySelector('[data-modal-caption]');
      const closeBtn = modal.querySelector('[data-modal-close]');

      grid.querySelectorAll('.gallery-item').forEach((item) => {
        item.addEventListener('click', () => {
          const frame = item.querySelector('.photo-frame');
          const caption = item.getAttribute('data-caption') || '';
          const imageUrl = item.getAttribute('data-image');

          if (imageUrl && modalPhoto) {
            // Real photo: use an actual <img> so it sizes to its own
            // aspect ratio and never gets cropped (object-fit: contain).
            modalPhoto.src = imageUrl;
            modalPhoto.alt = caption;
            modalPhoto.style.display = 'block';
            if (modalImg) modalImg.style.display = 'none';
          } else if (modalImg) {
            // No real photo: fall back to the colored placeholder tone.
            const tone = frame ? frame.className : '';
            modalImg.className = 'photo-frame ' + (tone.match(/tone-\w+/) || [''])[0];
            modalImg.style.display = 'block';
            if (modalPhoto) modalPhoto.style.display = 'none';
          }
          if (modalCaption) modalCaption.textContent = caption;
          modal.classList.add('is-open');
          document.body.style.overflow = 'hidden';
        });
      });

      const closeModal = () => {
        modal.classList.remove('is-open');
        document.body.style.overflow = '';
      };

      if (closeBtn) closeBtn.addEventListener('click', closeModal);
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
      });
    }
  }

  async function init() {
    if (window.KilkaariAPI) {
      try {
        const items = await window.KilkaariAPI.getGallery();
        if (Array.isArray(items) && items.length > 0) {
          const sorted = items.slice().sort((a, b) => (a.display_order || 0) - (b.display_order || 0));
          renderItems(sorted);
        }
        // If the API returns an empty list, keep the static placeholder
        // markup already in the page rather than showing a blank grid.
      } catch (err) {
        // Backend unreachable / erroring — keep the static placeholder
        // markup that's already in gallery.html so the page still looks fine.
        console.warn('Gallery API unavailable, showing placeholder content:', err.message);
      }
    }
    wireUpInteractions();
  }

  init();
})();
