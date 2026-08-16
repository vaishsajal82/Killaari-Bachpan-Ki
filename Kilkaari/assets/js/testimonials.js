/* ==========================================================================
   testimonials.js — auto-advancing testimonial slider with dot navigation.
   Exposed as window.KilkaariTestimonials.init() so home.js can rebuild the
   slider after swapping in live data from the backend, without duplicating
   this logic.
   ========================================================================== */

(function () {
  let timer = null;

  function init() {
    const track = document.querySelector('.testimonial-track');
    const dotsWrap = document.querySelector('.testimonial-dots');
    if (!track || !dotsWrap) return;

    clearInterval(timer);
    dotsWrap.innerHTML = '';

    const slides = track.children;
    if (!slides.length) return;
    let index = 0;

    const goTo = (i) => {
      index = (i + slides.length) % slides.length;
      track.style.transform = `translateX(-${index * 100}%)`;
      [...dotsWrap.children].forEach((d, di) => d.classList.toggle('active', di === index));
    };

    [...slides].forEach((_, i) => {
      const dot = document.createElement('button');
      dot.setAttribute('aria-label', `Show testimonial ${i + 1}`);
      if (i === 0) dot.classList.add('active');
      dot.addEventListener('click', () => {
        goTo(i);
        restart();
      });
      dotsWrap.appendChild(dot);
    });

    track.style.display = 'flex';
    track.style.transition = 'transform .5s ease';
    [...slides].forEach((s) => (s.style.minWidth = '100%'));

    function restart() {
      clearInterval(timer);
      if (slides.length > 1) timer = setInterval(() => goTo(index + 1), 6000);
    }

    goTo(0);
    restart();
  }

  window.KilkaariTestimonials = { init };
  init(); // run once immediately against whatever's in the DOM right now
           // (static fallback content) — home.js calls init() again if/when
           // it swaps in real testimonials from the backend.
})();
