# Kilkaari – Bachpan Ki — Public Website

Static HTML/CSS/JS public site for Kilkaari – Bachpan Ki, an NGO working
for children through education, healthcare awareness, nutrition, skill
development, women empowerment and community welfare.

All 8 pages are built (`index`, `about`, `programs`, `events`, `gallery`,
`donate`, `volunteer`, `contact`). Programs, Events, Gallery, and the
Centers section of About pull **live data from the backend API** on load
(see `assets/js/api.js`, and the per-page scripts like `events.js`,
`gallery.js`, `home.js`) and fall back to the static placeholder markup
already in the HTML if the backend is unreachable. Contact, Volunteer, and
Donate submit real form data to the backend.

## Stack
HTML5, CSS3 (no framework), vanilla ES6 JavaScript. No build step — open
any page directly in a browser or serve the folder with any static file
server.

## Structure
- `assets/css/` — one stylesheet per concern (global tokens, navbar, hero,
  cards, buttons, forms, footer, responsive overrides — loaded last)
- `assets/js/` — one script per feature/page (`api.js` is the shared fetch
  wrapper every other script builds on; `navbar.js`, `hero.js`,
  `counter.js`, `gallery.js`, `events.js`, `home.js`, `faq.js`,
  `testimonials.js`, `carousel.js`, `animation.js` for scroll-reveal)
- `assets/images/` — logo, favicon (`favicon.ico`, `favicon-32.png`,
  `apple-touch-icon.png`), background pattern; content images themselves
  live on Cloudinary once uploaded through the admin portal, not here
- `robots.txt`, `sitemap.xml` — basic SEO config. **Both contain a
  `REPLACE-WITH-YOUR-DOMAIN.com` placeholder** — update once you have a
  real deployed domain, along with the `og:url`/`og:image` meta tags in
  each page's `<head>` (search each HTML file for `TODO`)

## Connecting to the backend
Every page loads `assets/js/api.js` first, which points at
`https://killaari-bachpan-ki.onrender.com` by default. To point at a
different backend (e.g. running locally), set
`window.KILKAARI_API_BASE_URL` in a `<script>` tag before `api.js` loads.

## Design system
- Colors: Primary `#0D6EFD`, Secondary `#2E8B57`, Accent `#F4B400`,
  Background `#FAFAFA`, Dark `#2C2C2C`, Light `#FFFFFF`
- Type: Poppins (headings/display), Open Sans (body)
- Radius: 12px · Shadows: soft, realistic, no glassmorphism

## Known gaps
- No automated accessibility or cross-browser/responsive testing has been
  run against these pages — only code-level review. Worth a manual pass
  with a screen reader and real devices before treating this as fully
  accessible/responsive-verified.
- `og:url`/`og:image`/sitemap/robots.txt all reference a placeholder
  domain until you fill in your real one.
