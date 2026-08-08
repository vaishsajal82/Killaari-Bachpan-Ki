from app.models import Testimonial
from app.routers.crud_factory import build_crud_router
from app.schemas import TestimonialCreate, TestimonialOut, TestimonialUpdate

router = build_crud_router(
    prefix="/api/testimonials",
    tag="testimonials",
    model=Testimonial,
    create_schema=TestimonialCreate,
    update_schema=TestimonialUpdate,
    out_schema=TestimonialOut,
    published_only_field="is_published",
    order_by="created_at",
    order_desc=True,
)
