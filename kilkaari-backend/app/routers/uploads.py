"""
uploads.py — lets the admin portal upload an actual image file (instead of
having to already have it hosted somewhere and paste a direct URL). The file
is saved to disk under app/static/uploads and served back at
/uploads/<filename>, and this endpoint returns the full URL so it can be
dropped straight into any image_url field (gallery, programs, events,
campaigns, testimonials, student stories).
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File

from app.auth import require_admin
from app.models import User

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("", status_code=201)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    _admin: User = Depends(require_admin),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File is too large (max 8 MB).")

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename
    dest.write_bytes(contents)

    # request.base_url reflects wherever this API is actually being served
    # from (localhost during dev, the real domain in production), so the
    # returned URL always resolves correctly without extra config.
    url = f"{str(request.base_url).rstrip('/')}/uploads/{filename}"
    return {"url": url}
