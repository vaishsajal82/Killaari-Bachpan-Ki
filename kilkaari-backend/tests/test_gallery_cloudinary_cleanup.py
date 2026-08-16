"""
Verifies the gallery update/delete Cloudinary-cleanup hook LOGIC end-to-end
against the real app, real routes, real database — the only thing
substituted is the actual outbound network call to Cloudinary, since no
real Cloudinary credentials are available in this environment. This is
NOT a substitute for testing against the real Cloudinary API; see the
final report for what that still requires.
"""
import os
import sys

os.environ["DATABASE_URL"] = f"sqlite:///{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/kilkaari_hook_test.db"
os.environ["FIRST_ADMIN_PASSWORD"] = "testpass123"
os.environ["CORS_ORIGINS"] = "*"

# The "app" package lives at the repo root (kilkaari-backend/), one level
# up from this file's own directory (kilkaari-backend/tests/) — insert
# the parent, not this directory itself, or `from app...` imports fail.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.database import Base, engine
from app.main import app

Base.metadata.create_all(bind=engine)  # sidestep alembic for this throwaway test db

client = TestClient(app)

deleted_public_ids = []


def fake_delete_image(public_id):
    deleted_public_ids.append(public_id)
    return True


upload_call_count = [0]


def fake_upload_image_bytes(contents, *, folder):
    upload_call_count[0] += 1
    return {
        "url": f"https://res.cloudinary.com/demo/image/upload/fake_{upload_call_count[0]}.jpg",
        "public_id": f"kilkaari/uploads/fake_{upload_call_count[0]}",
        "width": 800, "height": 600, "format": "jpg",
    }


with patch("app.routers.uploads.upload_image_bytes", side_effect=fake_upload_image_bytes), \
     patch("app.routers.gallery.delete_image", side_effect=fake_delete_image), \
     client:

    login_resp = client.post("/api/auth/login", json={
        "email": "admin@kilkaari.org.in", "password": "testpass123",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # --- upload #1, create gallery item with it ---
    jpeg_bytes = bytes([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10]) + b"JFIF" + bytes(20)
    up1 = client.post("/api/uploads", files={"file": ("a.jpg", jpeg_bytes, "image/jpeg")}, headers=headers).json()
    assert up1["public_id"] == "kilkaari/uploads/fake_1", up1

    item = client.post("/api/gallery", json={
        "title": "Test", "image_url": up1["url"], "cloudinary_public_id": up1["public_id"],
    }, headers=headers).json()
    print("PASS: created gallery item with fake_1")

    # --- edit WITHOUT changing the image (e.g. just the caption) ---
    client.put(f"/api/gallery/{item['id']}", json={"caption": "new caption"}, headers=headers)
    assert deleted_public_ids == [], f"Should NOT have deleted anything yet, got: {deleted_public_ids}"
    print("PASS: editing caption only did not trigger any Cloudinary delete")

    # --- upload #2 (replacement image), update item with it ---
    up2 = client.post("/api/uploads", files={"file": ("b.jpg", jpeg_bytes, "image/jpeg")}, headers=headers).json()
    client.put(f"/api/gallery/{item['id']}", json={
        "image_url": up2["url"], "cloudinary_public_id": up2["public_id"],
    }, headers=headers)
    assert deleted_public_ids == ["kilkaari/uploads/fake_1"], \
        f"Expected old image (fake_1) deleted after replacement, got: {deleted_public_ids}"
    print("PASS: replacing the image correctly deleted the OLD Cloudinary asset (fake_1), not the new one")

    # --- delete the item entirely ---
    client.delete(f"/api/gallery/{item['id']}", headers=headers)
    assert deleted_public_ids == ["kilkaari/uploads/fake_1", "kilkaari/uploads/fake_2"], \
        f"Expected fake_2 also deleted after item delete, got: {deleted_public_ids}"
    print("PASS: deleting the gallery item deleted its current Cloudinary asset (fake_2)")

    # --- item with NO public_id (e.g. a manually pasted external URL) — delete must not crash ---
    item2 = client.post("/api/gallery", json={
        "image_url": "https://example.com/external-photo.jpg",
    }, headers=headers).json()
    before = len(deleted_public_ids)
    resp = client.delete(f"/api/gallery/{item2['id']}", headers=headers)
    assert resp.status_code == 204
    assert len(deleted_public_ids) == before, "Should not attempt a Cloudinary delete for an item with no public_id"
    print("PASS: deleting an item with no cloudinary_public_id (external URL) works fine and skips cleanup")

print("\nALL HOOK-LOGIC TESTS PASSED")
