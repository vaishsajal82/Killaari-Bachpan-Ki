"""
main.py — FastAPI application entrypoint for the Kilkaari backend.

Run locally with:
    uvicorn app.main:app --reload

Interactive API docs are then available at /docs (Swagger) and /redoc.
"""

from pathlib import Path

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import settings
from app.database import SessionLocal
from app.models import User, UserRole
from app.rate_limit import limiter
from app.routers import (
    admin, auth, campaigns, centers, contact, donations, events,
    gallery, newsletter, programs, stories, testimonials, uploads, volunteers,
)

logger = logging.getLogger("kilkaari")

app = FastAPI(
    title="Kilkaari – Bachpan Ki API",
    description="Backend API for the Kilkaari NGO website: forms, donations, "
                 "content management and an admin dashboard.",
    version="1.0.0",
)

# Rate limiting — see app/rate_limit.py for the shared Limiter, and each
# router (auth, contact, donations, volunteers, newsletter) for the actual
# per-endpoint limits. This wiring (state + exception handler + middleware)
# is what makes the @limiter.limit(...) decorators on those routes work.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    # A raw SQLAlchemy exception's message can include table/column names,
    # the offending SQL, or the connection string — never let that reach a
    # client. Logged in full server-side (visible in Render's Logs tab)
    # where it's actually useful; the client gets a generic message only.
    logger.exception("Unhandled database error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "A database error occurred. Please try again."})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    # Final safety net for anything not already handled above or by
    # FastAPI's own HTTPException/RequestValidationError handling — a
    # genuinely unexpected bug should never hand the client a Python
    # traceback, file paths, or internal state. FastAPI's default behavior
    # already doesn't leak this (it returns a bare 500 with no detail), but
    # this makes that guarantee explicit in this project's own code rather
    # than relying entirely on framework defaults, and ensures every
    # unhandled exception is actually logged server-side for debugging.
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong. Please try again."})


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Sets standard defensive headers on every response.

    /docs, /redoc, and /openapi.json are excluded from the CSP: Swagger UI
    and ReDoc load their JS/CSS from a CDN (cdn.jsdelivr.net) and use
    inline scripts to bootstrap, which a strict CSP would break. Every
    other route on this API only ever returns JSON, never renders HTML
    from user input, so a tight default-src 'none' CSP is both safe and
    the correct choice there — this is a pure JSON API, not an HTML app,
    so there's no legitimate reason for a browser to execute a script or
    load a subresource in the context of any of these responses at all.
    """
    response = await call_next(request)

    is_docs = request.url.path in ("/docs", "/redoc", "/openapi.json")
    if not is_docs:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # Harmless to send even over plain HTTP during local dev — browsers only
    # honor HSTS when the connection is actually HTTPS, which it always is
    # once this is deployed behind Render's TLS termination.
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


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
    # This MUST stay False as long as auth is Bearer-token-in-header based
    # (see app/auth.py — that's the only auth mechanism in this app; there
    # is no cookie-based session anywhere). allow_credentials=True is what
    # makes cookies get sent cross-origin, which is also what makes CSRF
    # possible in the first place — a Bearer token in an Authorization
    # header must be explicitly attached by the calling JavaScript, so a
    # malicious third-party page can't make an authenticated request just
    # by getting a logged-in admin to visit it, the way it could with
    # cookie auth. If this project ever moves auth to httpOnly cookies,
    # that change and CSRF protection (double-submit token or a framework
    # CSRF middleware) must land together — do not flip allow_credentials
    # to True without it.
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

# Backward compatibility only — POST /api/uploads no longer writes here
# (new uploads go to Cloudinary; see app/cloudinary_service.py and
# app/routers/uploads.py). This mount stays so any image_url saved before
# that migration, of the form ".../uploads/<filename>", keeps resolving
# instead of breaking. Safe to remove once no gallery_items (or other
# content) rows still reference a URL under this path — until then, this
# directory won't gain new files, but shouldn't be deleted.
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
