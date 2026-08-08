from app.models import Program
from app.routers.crud_factory import build_crud_router
from app.schemas import ProgramCreate, ProgramOut, ProgramUpdate

router = build_crud_router(
    prefix="/api/programs",
    tag="programs",
    model=Program,
    create_schema=ProgramCreate,
    update_schema=ProgramUpdate,
    out_schema=ProgramOut,
    published_only_field="is_published",
    order_by="display_order",
)
