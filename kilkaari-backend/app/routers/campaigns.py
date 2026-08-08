from app.models import Campaign
from app.routers.crud_factory import build_crud_router
from app.schemas import CampaignCreate, CampaignOut, CampaignUpdate

router = build_crud_router(
    prefix="/api/campaigns",
    tag="campaigns",
    model=Campaign,
    create_schema=CampaignCreate,
    update_schema=CampaignUpdate,
    out_schema=CampaignOut,
    published_only_field="is_active",
    order_by="created_at",
    order_desc=True,
)
