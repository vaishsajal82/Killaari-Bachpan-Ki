/* ==========================================================================
   hero.js — subtle hero entrance sequencing
   ========================================================================== */

(function () {
  const hero = document.querySelector('.hero');
  if (!hero) return;

  const items = hero.querySelectorAll('[data-hero-item]');
  items.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    el.style.transition = 'opacity .6s ease, transform .6s ease';
    setTimeout(() => {
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, 120 + i * 110);
  });
})();
