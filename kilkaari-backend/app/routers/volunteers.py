from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VolunteerApplication
from app.rate_limit import limiter
from app.schemas import VolunteerApplicationCreate, VolunteerApplicationOut

router = APIRouter(prefix="/api/volunteer-applications", tags=["volunteers"])


@router.post("", response_model=VolunteerApplicationOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def submit_application(request: Request, payload: VolunteerApplicationCreate, db: Session = Depends(get_db)):
    application = VolunteerApplication(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application
