"""
gallery.py — gallery CRUD, built on the generic crud_factory with two extra
hooks so replacing or deleting a gallery item's image also cleans up the
old Cloudinary asset instead of leaving it orphaned forever.
"""

import logging

from app.cloudinary_service import delete_image
from app.models import GalleryItem
from app.routers.crud_factory import build_crud_router
from app.schemas import GalleryItemCreate, GalleryItemOut, GalleryItemUpdate

logger = logging.getLogger("kilkaari.gallery")


def _cleanup_old_image_on_update(item: GalleryItem, old_values: dict) -> None:
    """Runs after a gallery item is successfully updated. If the image was
    actually replaced (image_url changed) and the item had an old
    Cloudinary asset, delete that old asset now that the new one is safely
    saved in the database — never delete the old image before the new one
    is confirmed persisted, so a failed/interrupted edit can't lose both.
    """
    old_public_id = old_values.get("cloudinary_public_id")
    image_was_changed = "image_url" in old_values and old_values["image_url"] != item.image_url
    if image_was_changed and old_public_id and old_public_id != item.cloudinary_public_id:
        delete_image(old_public_id)  # best-effort; logs internally on failure


def _cleanup_image_on_delete(deleted_row: dict) -> None:
    """Runs after a gallery item is successfully deleted. Cleans up its
    Cloudinary asset, if it had one."""
    public_id = deleted_row.get("cloudinary_public_id")
    if public_id:
        delete_image(public_id)  # best-effort; logs internally on failure


router = build_crud_router(
    prefix="/api/gallery",
    tag="gallery",
    model=GalleryItem,
    create_schema=GalleryItemCreate,
    update_schema=GalleryItemUpdate,
    out_schema=GalleryItemOut,
    order_by="display_order",
    after_update=_cleanup_old_image_on_update,
    after_delete=_cleanup_image_on_delete,
)
