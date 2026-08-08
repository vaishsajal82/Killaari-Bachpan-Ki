from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VolunteerApplication
from app.schemas import VolunteerApplicationCreate, VolunteerApplicationOut

router = APIRouter(prefix="/api/volunteer-applications", tags=["volunteers"])


@router.post("", response_model=VolunteerApplicationOut, status_code=status.HTTP_201_CREATED)
def submit_application(payload: VolunteerApplicationCreate, db: Session = Depends(get_db)):
    application = VolunteerApplication(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application
