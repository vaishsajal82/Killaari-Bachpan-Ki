"""
main.py — FastAPI application entrypoint for the Kilkaari backend.

Run locally with:
    uvicorn app.main:app --reload

Interactive API docs are then available at /docs (Swagger) and /redoc.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import settings
from app.database import SessionLocal
from app.models import User, UserRole
from app.routers import (
    admin, auth, campaigns, centers, contact, donations, events,
    gallery, newsletter, programs, stories, testimonials, uploads, volunteers,
)

app = FastAPI(
    title="Kilkaari – Bachpan Ki API",
    description="Backend API for the Kilkaari NGO website: forms, donations, "
                 "content management and an admin dashboard.",
    version="1.0.0",
)

_cors_origins = settings.cors_origin_list
_wildcard_dev_mode = _cors_origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    # In production, CORS_ORIGINS in .env must be an explicit comma-separated
    # list of real frontend/admin URLs (e.g. https://kilkaari.org,
    # https://admin.kilkaari.org) — never "*". Wildcard is only for local
    # dev convenience, set deliberately via CORS_ORIGINS=* in your local .env.
    allow_origins=["*"] if _wildcard_dev_mode else _cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(donations.router)
app.include_router(volunteers.router)
app.include_router(contact.router)
app.include_router(newsletter.router)
app.include_router(programs.router)
app.include_router(events.router)
app.include_router(campaigns.router)
app.include_router(gallery.router)
app.include_router(testimonials.router)
app.include_router(centers.router)
app.include_router(stories.router)
app.include_router(admin.router)
app.include_router(uploads.router)

# Serves files saved by uploads.router at /uploads/<filename>, so an
# image_url returned from POST /api/uploads actually resolves.
_static_uploads_dir = Path(__file__).resolve().parent / "static" / "uploads"
_static_uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_static_uploads_dir)), name="uploads")


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok"}


@app.get("/", tags=["health"])
def root():
    # A plain root route so hitting the bare domain (e.g. Render's own
    # health pings, or someone opening the URL in a browser to sanity-check
    # it's alive) returns something meaningful instead of a 404 — the API
    # itself always lived under /api/* and /docs, but an unhandled "/" made
    # it look broken even when everything was actually fine.
    return {
        "service": "Kilkaari – Bachpan Ki API",
        "status": "ok",
        "docs": "/docs",
    }


def _ensure_first_admin(db: Session) -> None:
    admin_exists = db.query(User).filter(User.role == UserRole.admin).first()
    if admin_exists:
        return
    admin_user = User(
        full_name=settings.first_admin_name,
        email=settings.first_admin_email,
        hashed_password=hash_password(settings.first_admin_password),
        role=UserRole.admin,
    )
    db.add(admin_user)
    db.commit()


@app.on_event("startup")
def on_startup():
    # Table creation is now handled by Alembic migrations (`alembic upgrade
    # head`) instead of create_all(), so schema changes are tracked and
    # reversible. Run migrations before starting the app — see README.
    db = SessionLocal()
    try:
        _ensure_first_admin(db)
    finally:
        db.close()

    # Printed on every boot (visible in Render's Logs tab) specifically so a
    # CORS-related "can't reach the backend" report from the frontend can be
    # diagnosed in seconds instead of guessing — if the admin/site origin
    # isn't in this list and it isn't "*", that's the bug.
    print(f"[startup] CORS allowed origins: {_cors_origins if not _wildcard_dev_mode else ['*']}")
