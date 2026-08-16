# tests/

Not wired into a pytest suite/CI yet — run directly:

    python tests/test_gallery_cloudinary_cleanup.py

test_gallery_cloudinary_cleanup.py verifies the gallery image-replace/delete
Cloudinary cleanup logic (crud_factory's after_update/after_delete hooks)
against the real app/routes/database, with only the actual outbound
Cloudinary network calls substituted for fakes — no real Cloudinary
credentials are required to run this.
