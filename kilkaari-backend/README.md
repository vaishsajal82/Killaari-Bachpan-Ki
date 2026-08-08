# Kilkaari – Bachpan Ki — Backend API

A FastAPI + PostgreSQL backend for the Kilkaari website: contact/volunteer
forms, donations (with a pluggable payment gateway), user accounts, and an
admin panel API to manage all site content.

## Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL, via SQLAlchemy + the psycopg3 driver
- **Migrations:** Alembic (schema is version-controlled, not auto-created)
- **Auth:** JWT bearer tokens, bcrypt password hashing
- **Docs:** auto-generated at `/docs` (Swagger UI) and `/redoc`

## Quick start

```bash
cd kilkaari-backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .env.example .env
# edit .env — set DATABASE_URL to a real Postgres connection string (see
# "Database" section below for how to create one), plus JWT_SECRET_KEY and
# the FIRST_ADMIN_* values (that admin account is created automatically the
# first time the app starts, if no admin exists yet)

alembic upgrade head     # creates all tables
python run.py
# or: uvicorn app.main:app --reload
```

Then open **http://localhost:8000/docs** to try every endpoint interactively.

Optional — load real Kilkaari content (programs, centers, student stories)
pulled from the live site so the API isn't empty on first run:
```bash
python seed.py
```

## Database — PostgreSQL

This backend runs on PostgreSQL, using SQLAlchemy with the **psycopg3** driver, and Alembic for schema migrations.

### Local setup (no Docker)
```bash
brew install postgresql@16
brew services start postgresql@16
createuser kilkaari_user --pwprompt      # set a password when prompted
createdb kilkaari --owner=kilkaari_user
```
Set in `.env`:
```
DATABASE_URL=postgresql+psycopg://kilkaari_user:yourpassword@localhost:5432/kilkaari
```
Then apply migrations:
```bash
alembic upgrade head
```

### Docker setup
See the root-level `docker-compose.yml` (outside this folder) — it runs Postgres in a container and the backend automatically runs `alembic upgrade head` on startup via `entrypoint.sh` before the server starts. No manual migration step needed with Docker.

### Making schema changes going forward
Whenever you add/change a model in `app/models.py`:
```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```
Always review the auto-generated migration file in `alembic/versions/` before applying it — autogenerate is very good but not infallible (e.g. it won't detect some column renames correctly).

### Fresh SQLite for a quick local play session (not recommended beyond that)
If you just want to poke at the API without setting up Postgres at all, you can still set `DATABASE_URL=sqlite:///./kilkaari_dev.db` — but you'd then need to bring back `Base.metadata.create_all()` in `main.py` (currently removed in favor of Alembic) since Alembic migrations here were generated against Postgres. For any real use, Postgres is the supported path.

## Authentication
- `POST /api/auth/register` — creates a `donor` account, returns a JWT
- `POST /api/auth/login` — returns a JWT
- `GET /api/auth/me` — current user (send `Authorization: Bearer <token>`)

An **admin** account can't self-register through the API. The first admin
is created automatically from `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD`
in `.env`. Promote further admins directly in the database, or add a
protected "promote user" endpoint if you need one later.

## Public endpoints (no login required)
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/donations` | Start a donation (guest or logged in) |
| POST | `/api/donations/{id}/confirm-test-payment` | Simulate success in test mode |
| POST | `/api/volunteer-applications` | Submit a volunteer application |
| POST | `/api/contact-messages` | Submit the contact form |
| POST | `/api/newsletter/subscribe` | Newsletter signup |
| GET | `/api/programs`, `/api/events`, `/api/campaigns`, `/api/gallery`, `/api/testimonials`, `/api/centers`, `/api/student-stories` | Public content, published items only |

## Admin-only endpoints (JWT with `role: admin`)
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/admin/dashboard` | Totals: donations, applications, messages, subscribers |
| GET | `/api/admin/donations` | All donations |
| GET / PATCH | `/api/admin/volunteer-applications` | Review applications, update status |
| GET / PATCH | `/api/admin/contact-messages` | Read inbox, mark as read |
| GET / PATCH | `/api/admin/users` | List users, deactivate an account |
| POST / PUT / DELETE | `/api/programs`, `/api/events`, `/api/campaigns`, `/api/gallery`, `/api/testimonials`, `/api/centers`, `/api/student-stories` | Manage site content |

## Payments
Donations work end-to-end out of the box using a **test provider**
(`PAYMENT_PROVIDER=test` in `.env`) that always succeeds — useful for
building and demoing the donor flow before a real gateway is connected.

`app/payments.py` defines a small provider interface with stubs for
**Razorpay** and **Instamojo** (the live kilkaari.org.in site already uses
Instamojo for its `/donate/` page, so that's the most likely one to finish
first). Fill in the matching API keys in `.env`, then implement the two
`TODO`s in the relevant provider class.

## Project layout
```
kilkaari-backend/
├── app/
│   ├── main.py            # FastAPI app, router wiring, first-admin bootstrap
│   ├── config.py          # settings loaded from .env
│   ├── database.py        # SQLAlchemy engine/session
│   ├── models.py           # ORM models (User, Donation, Program, ...)
│   ├── schemas.py          # Pydantic request/response models
│   ├── auth.py             # password hashing, JWT, auth dependencies
│   ├── payments.py         # payment provider abstraction (test/Razorpay/Instamojo)
│   └── routers/
│       ├── auth.py, donations.py, volunteers.py, contact.py, newsletter.py
│       ├── programs.py, events.py, campaigns.py, gallery.py,
│       │   testimonials.py, centers.py, stories.py   # built on crud_factory.py
│       ├── crud_factory.py   # shared public-read/admin-write CRUD builder
│       └── admin.py           # dashboard + oversight endpoints
├── alembic/                 # database migrations (alembic upgrade head)
│   ├── env.py               # wired to app.models + .env's DATABASE_URL
│   └── versions/
├── seed.py                 # loads real Kilkaari content for a fresh DB
├── reset_admin.py          # update the existing admin's email/password from .env
├── run.py                  # `python run.py` to start the dev server
├── entrypoint.sh            # Docker entrypoint: runs migrations, then starts uvicorn
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Connecting the frontend
The existing static frontend (`Kilkaari/`) currently has no JavaScript
`fetch()` calls wired up — its forms just show a success message locally.
To connect them:
1. Set `CORS_ORIGINS` in `.env` to wherever the frontend is served from.
2. In `assets/js/main.js`, replace the `data-demo-form` handler with a real
   `fetch('http://localhost:8000/api/contact-messages', { method: 'POST', ... })`
   call (same pattern for the volunteer and newsletter forms, and for
   donations on `donate.html`).
