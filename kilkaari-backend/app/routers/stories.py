from app.models import StudentStory
from app.routers.crud_factory import build_crud_router
from app.schemas import StudentStoryCreate, StudentStoryOut, StudentStoryUpdate

router = build_crud_router(
    prefix="/api/student-stories",
    tag="student-stories",
    model=StudentStory,
    create_schema=StudentStoryCreate,
    update_schema=StudentStoryUpdate,
    out_schema=StudentStoryOut,
    published_only_field="is_published",
    order_by="created_at",
    order_desc=True,
)
