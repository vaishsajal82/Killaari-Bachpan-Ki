from app.models import GalleryItem
from app.routers.crud_factory import build_crud_router
from app.schemas import GalleryItemCreate, GalleryItemOut, GalleryItemUpdate

router = build_crud_router(
    prefix="/api/gallery",
    tag="gallery",
    model=GalleryItem,
    create_schema=GalleryItemCreate,
    update_schema=GalleryItemUpdate,
    out_schema=GalleryItemOut,
    order_by="display_order",
)
