# Kilkaari – Bachpan Ki

A full-stack website for Kilkaari – Bachpan Ki, an NGO working for
children through education, healthcare awareness, nutrition, skill
development, women empowerment, and community welfare.

This is the top-level overview. Each of the three parts below has its own,
more detailed README.

## Architecture

```
Kilkaari/            Public website — static HTML/CSS/JS, no build step.
                      Fetches live content (programs, events, gallery,
                      centers) from the backend API; falls back to static
                      placeholder content if the backend is unreachable.
                      → Kilkaari/README.md

kilkaari-admin/       Admin portal — static HTML/CSS/JS. Login, dashboard,
                      and full CRUD for every content type, donations,
                      volunteer applications, contact messages, and users.

kilkaari-backend/     FastAPI + PostgreSQL API. Auth, all content CRUD,
                      donations, image uploads (Cloudinary), rate
                      limiting, security headers.
                      → kilkaari-backend/README.md

scripts/               Project-wide tooling (currently: dependency
                      vulnerability scanning — see security-audit.sh)

.github/workflows/    CI — runs the dependency audit on every push/PR
```

Nothing here uses a frontend framework (no React/Vue/etc.) — the public
site and admin portal are both hand-written vanilla JS calling the backend
API directly with `fetch()`.

## Deployment (current, as configured in this repo)
- **Backend** → Render (Python web service)
- **Admin portal** → Vercel
- **Database** → Neon (managed PostgreSQL, separate from Render)
- **Image storage** → Cloudinary
- **Public website** → not yet deployed anywhere permanent as of this
  writing; `Kilkaari/` is ready to deploy to any static host (Vercel,
  Netlify, GitHub Pages, etc.)

## Local development — quick start

```bash
# 1. Backend
cd kilkaari-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in DATABASE_URL, JWT_SECRET_KEY,
                             # FIRST_ADMIN_*, and (for image uploads)
                             # CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET
alembic upgrade head
python run.py                # → http://localhost:8000, docs at /docs

# 2. Admin portal (separate terminal)
cd kilkaari-admin
python -m http.server 5500   # or any static file server
# → http://localhost:5500 — set window.KILKAARI_API_BASE_URL if your
#   backend isn't on the default Render URL admin.js points to

# 3. Public site (separate terminal)
cd Kilkaari
python -m http.server 5501
# → http://localhost:5501
```

See `kilkaari-backend/README.md` for full environment variable docs,
database setup options, and the complete API reference.

## Security posture (summary — see kilkaari-backend/README.md for detail)
- JWT bearer-token auth (no cookies — CSRF isn't applicable to this
  architecture; see the comment on `allow_credentials` in `app/main.py`)
- Rate limiting on login, contact/volunteer forms, donations
- Real security headers (CSP, HSTS, etc.) on every API response
- File uploads validated by actual file content (magic bytes), not
  filename/extension — rejects disguised malicious files
- Global exception handling — no stack traces, DB errors, or internal
  paths ever reach a client response
- `scripts/security-audit.sh` (also runs in CI) scans dependencies for
  known vulnerabilities

## Known limitations — read before treating this as fully production-ready
- **No real payment gateway is implemented.** Donations run through a
  test-mode provider that always succeeds; Razorpay/Instamojo integration
  exists only as unfinished stubs in `app/payments.py`.
- **No automated tests run in CI** beyond the dependency audit — there's
  one manual regression test for the Cloudinary gallery-cleanup logic
  (`kilkaari-backend/tests/`), not a full suite.
- **No accessibility or cross-browser/device testing has actually been
  performed** — only code-level review (semantic HTML, alt text,
  escaping). Verify manually before launch.
- `robots.txt`, `sitemap.xml`, and each page's Open Graph tags reference a
  `REPLACE-WITH-YOUR-DOMAIN.com` placeholder until the public site has a
  real deployed domain.
- Only Gallery items track their Cloudinary `public_id` for cleanup on
  delete/replace — other content types (Programs, Events, etc.) upload to
  Cloudinary too but don't yet clean up their old asset when replaced.
