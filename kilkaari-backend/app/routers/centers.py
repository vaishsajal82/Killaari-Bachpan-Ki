from app.models import Center
from app.routers.crud_factory import build_crud_router
from app.schemas import CenterCreate, CenterOut, CenterUpdate

router = build_crud_router(
    prefix="/api/centers",
    tag="centers",
    model=Center,
    create_schema=CenterCreate,
    update_schema=CenterUpdate,
    out_schema=CenterOut,
    order_by="created_at",
)
