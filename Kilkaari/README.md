# Kilkaari – Bachpan Ki

Frontend-only website for Kilkaari – Bachpan Ki, an NGO working for children through
education, healthcare awareness, nutrition, skill development, women empowerment and
community welfare.

## Stack
HTML5, CSS3 (no framework), vanilla ES6 JavaScript. No build step — open any page
directly in a browser or serve the folder with any static file server.

## Structure
- `index.html` — homepage (delivered first; see below for remaining pages)
- `assets/css/` — one stylesheet per concern (global tokens, navbar, hero, cards,
  buttons, forms, footer, responsive overrides — loaded last)
- `assets/js/` — one script per feature (navbar, hero, counters, gallery, faq,
  testimonials, scroll-reveal animation, main/shared behavior)
- `assets/images/`, `assets/icons/` — reserved for real photography/icon assets;
  the current build uses styled `.photo-frame` placeholders so the site never
  depends on stock imagery you haven't chosen yet
- `components/` — standalone copies of repeated markup (navbar, footer, cards)
  for quick reuse when wiring up a CMS or template engine later

## Design system
- Colors: Primary `#0D6EFD`, Secondary `#2E8B57`, Accent `#F4B400`,
  Background `#FAFAFA`, Dark `#2C2C2C`, Light `#FFFFFF`
- Type: Poppins (headings/display), Open Sans (body)
- Radius: 12px · Shadows: soft, realistic, no glassmorphism

## Status
`index.html` is complete and production-ready. Remaining pages
(about, programs, events, gallery, volunteer, donate, contact) and the
`components/` partials are built next, one file at a time.
