from app.models import Event
from app.routers.crud_factory import build_crud_router
from app.schemas import EventCreate, EventOut, EventUpdate

router = build_crud_router(
    prefix="/api/events",
    tag="events",
    model=Event,
    create_schema=EventCreate,
    update_schema=EventUpdate,
    out_schema=EventOut,
    published_only_field="is_published",
    order_by="event_date",
)
