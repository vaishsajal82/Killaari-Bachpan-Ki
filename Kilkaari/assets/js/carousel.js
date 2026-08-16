/* ==========================================================================
   carousel.js — generic crossfade + swipe carousel controller
   Works on any .imgcarousel that contains .imgcarousel__slide children.
   Auto-builds dots + arrows, autoplays, and supports touch swipe.
   ========================================================================== */

(function () {
  function initCarousel(root, opts) {
    var settings = Object.assign({ interval: 4500 }, opts || {});
    var slides = Array.prototype.slice.call(root.querySelectorAll('.imgcarousel__slide'));
    if (slides.length <= 1) {
      if (slides[0]) slides[0].classList.add('is-active');
      return;
    }

    var index = 0;
    slides[0].classList.add('is-active');

    // ---- dots ----
    var dots = document.createElement('div');
    dots.className = 'imgcarousel__dots';
    var dotEls = slides.map(function (_, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('aria-label', 'Show image ' + (i + 1) + ' of ' + slides.length);
      if (i === 0) b.classList.add('is-active');
      b.addEventListener('click', function () { goTo(i); resetTimer(); });
      dots.appendChild(b);
      return b;
    });
    root.appendChild(dots);

    // ---- arrows ----
    var prevBtn = document.createElement('button');
    prevBtn.type = 'button';
    prevBtn.className = 'imgcarousel__arrow imgcarousel__arrow--prev';
    prevBtn.setAttribute('aria-label', 'Previous image');
    prevBtn.innerHTML = '&#10094;';
    var nextBtn = document.createElement('button');
    nextBtn.type = 'button';
    nextBtn.className = 'imgcarousel__arrow imgcarousel__arrow--next';
    nextBtn.setAttribute('aria-label', 'Next image');
    nextBtn.innerHTML = '&#10095;';
    root.appendChild(prevBtn);
    root.appendChild(nextBtn);
    prevBtn.addEventListener('click', function () { goTo(index - 1); resetTimer(); });
    nextBtn.addEventListener('click', function () { goTo(index + 1); resetTimer(); });

    function goTo(i) {
      slides[index].classList.remove('is-active');
      dotEls[index].classList.remove('is-active');
      index = (i + slides.length) % slides.length;
      slides[index].classList.add('is-active');
      dotEls[index].classList.add('is-active');
    }

    var timer;
    function resetTimer() {
      clearTimeout(timer);
      timer = setTimeout(function () { goTo(index + 1); resetTimer(); }, settings.interval);
    }
    resetTimer();

    // ---- touch swipe ----
    var startX = null;
    root.addEventListener('touchstart', function (e) {
      startX = e.touches[0].clientX;
    }, { passive: true });
    root.addEventListener('touchend', function (e) {
      if (startX === null) return;
      var dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 40) {
        goTo(dx < 0 ? index + 1 : index - 1);
        resetTimer();
      }
      startX = null;
    }, { passive: true });

    // pause autoplay while user hovers (desktop) so it doesn't fight manual browsing
    root.addEventListener('mouseenter', function () { clearTimeout(timer); });
    root.addEventListener('mouseleave', resetTimer);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.imgcarousel').forEach(function (el) {
      initCarousel(el, { interval: parseInt(el.dataset.interval, 10) || 4500 });
    });
  });
})();
