"""
uploads.py — lets the admin portal upload an actual image file (instead of
having to already have it hosted somewhere and paste a direct URL).

The file is uploaded to Cloudinary (see app/cloudinary_service.py) rather
than saved to local disk. This matters specifically because Render's
filesystem is NOT persistent — anything written to disk gets wiped on
every redeploy, so images saved locally would silently disappear the next
time the backend is pushed. Cloudinary is the actual persistent store now;
this endpoint just validates the upload and hands the bytes off to it.

This endpoint is shared by every content type's image field in the admin
portal (programs, events, campaigns, gallery, testimonials, student
stories) — not just gallery — so this migration benefits all of them
uniformly, not only the gallery feature that originally motivated it.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.auth import require_admin
from app.cloudinary_service import CloudinaryNotConfigured, CloudinaryUploadError, upload_image_bytes
from app.image_validation import sniff_image
from app.models import User

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB

# Cloudinary folder new uploads land in. Kept generic (not "gallery")
# since, per the note above, this one endpoint is shared across several
# content types, not gallery-specific.
CLOUDINARY_FOLDER = "kilkaari/uploads"


@router.post("", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    _admin: User = Depends(require_admin),
):
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File is too large (max 8 MB).")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Trust the actual bytes, not the filename or the client-supplied
    # Content-Type — both are attacker-controlled and easy to fake (e.g. a
    # renamed .html/.svg/.php file with a ".jpg" name and an "image/jpeg"
    # Content-Type header would sail past extension/MIME-header checks).
    # Unchanged from the previous local-disk implementation — this
    # validation matters just as much with Cloudinary as the destination.
    sniffed = sniff_image(contents)
    if sniffed is None:
        raise HTTPException(
            status_code=400,
            detail="This doesn't look like a valid JPEG, PNG, GIF, or WEBP image. "
                   "The file's actual content didn't match any of those formats.",
        )

    try:
        result = upload_image_bytes(contents, folder=CLOUDINARY_FOLDER)
    except CloudinaryNotConfigured:
        # 503, not 500 — this is a deployment/config problem (missing env
        # vars), not a bug or a bad request, and is worth distinguishing
        # in logs/monitoring from an actual Cloudinary-side failure.
        raise HTTPException(
            status_code=503,
            detail="Image uploads are not available right now (storage isn't configured). "
                   "Please contact the site administrator.",
        )
    except CloudinaryUploadError:
        raise HTTPException(status_code=502, detail="Image upload failed. Please try again.")

    return {
        "url": result["url"],
        "public_id": result["public_id"],
        "width": result["width"],
        "height": result["height"],
        "format": result["format"],
    }
