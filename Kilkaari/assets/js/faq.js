/* ==========================================================================
   faq.js — accessible accordion for FAQ sections
   ========================================================================== */

(function () {
  const items = document.querySelectorAll('.faq-item');
  if (!items.length) return;

  items.forEach((item) => {
    const question = item.querySelector('.faq-item__q');
    const answer = item.querySelector('.faq-item__a');

    question.addEventListener('click', () => {
      const isOpen = item.classList.contains('is-open');

      // Close all other items for a single-open accordion
      items.forEach((other) => {
        other.classList.remove('is-open');
        other.querySelector('.faq-item__q').setAttribute('aria-expanded', 'false');
        other.querySelector('.faq-item__a').style.maxHeight = null;
      });

      if (!isOpen) {
        item.classList.add('is-open');
        question.setAttribute('aria-expanded', 'true');
        answer.style.maxHeight = answer.scrollHeight + 'px';
      }
    });
  });
})();
