"""
cloudinary_service.py — thin wrapper around the Cloudinary Python SDK.

Keeps all Cloudinary-specific code (configuration, the actual upload/delete
calls, and how errors from those calls get translated into something safe
to show a client) in one place, so routers just call upload_image_bytes()
or delete_image() without needing to know anything about Cloudinary's SDK
directly.

The API secret (settings.cloudinary_api_secret) is read here from the
backend's own environment/settings only — it is never sent to, or
accepted from, the frontend in any form.
"""

import logging

import cloudinary
import cloudinary.uploader

from app.config import settings

logger = logging.getLogger("kilkaari.cloudinary")

_configured = False


class CloudinaryNotConfigured(Exception):
    """Raised when an upload is attempted but CLOUDINARY_* env vars are
    missing. Kept as its own exception (rather than a bare RuntimeError)
    so the router can catch it specifically and return a clear 503,
    distinct from a genuine upload failure."""
    pass


class CloudinaryUploadError(Exception):
    """Raised when Cloudinary itself rejects the upload or the
    request fails (network issue, invalid credentials, quota, etc.).
    The original exception is logged in full server-side; only this
    generic message is meant to reach the client."""
    pass


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    if not (settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret):
        raise CloudinaryNotConfigured(
            "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET "
            "must all be set as environment variables before uploads will work."
        )
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,  # always hand back https:// URLs
    )
    _configured = True


def upload_image_bytes(contents: bytes, *, folder: str) -> dict:
    """Uploads raw image bytes to Cloudinary and returns a dict with the
    fields callers actually need: url (the https secure_url), public_id,
    width, height, format.

    Raises CloudinaryNotConfigured if credentials aren't set, or
    CloudinaryUploadError if Cloudinary itself rejects/fails the upload —
    callers should catch both and turn them into an appropriate HTTP
    response rather than letting a raw SDK exception escape.
    """
    _ensure_configured()
    try:
        result = cloudinary.uploader.upload(
            contents,
            folder=folder,
            # Random unique public_id (Cloudinary's default when none is
            # given) — avoids collisions without needing to invent our own
            # naming scheme, and keeps no relationship to the original
            # filename (which is attacker-controlled input we don't trust
            # — see the filename-injection note in uploads.py).
            resource_type="image",
            overwrite=False,
        )
    except Exception as exc:  # cloudinary.exceptions.Error and friends
        # Never let a raw Cloudinary/network exception (which can include
        # request details) propagate to the client — log it fully here,
        # server-side only, and raise our own generic exception instead.
        logger.exception("Cloudinary upload failed")
        raise CloudinaryUploadError("The image upload failed. Please try again.") from exc

    return {
        "url": result["secure_url"],
        "public_id": result["public_id"],
        "width": result.get("width"),
        "height": result.get("height"),
        "format": result.get("format"),
    }


def delete_image(public_id: str) -> bool:
    """Best-effort delete of a Cloudinary asset. Returns True on success,
    False on failure — deliberately does not raise, because callers use
    this for cleanup (deleting the old image after a successful replace,
    or after a DB record is deleted) where the database operation has
    already succeeded and must not be treated as failed just because
    Cloudinary cleanup didn't go through. Failures are logged so an
    orphaned asset can still be found and cleaned up manually later.
    """
    try:
        _ensure_configured()
    except CloudinaryNotConfigured:
        logger.warning("Skipped Cloudinary delete for %s — Cloudinary is not configured.", public_id)
        return False

    try:
        cloudinary.uploader.destroy(public_id, resource_type="image")
        return True
    except Exception:
        logger.exception("Cloudinary delete failed for public_id=%s (leaving asset orphaned)", public_id)
        return False
