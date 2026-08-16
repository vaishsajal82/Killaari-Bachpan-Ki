from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContactMessage
from app.rate_limit import limiter
from app.schemas import ContactMessageCreate, ContactMessageOut

router = APIRouter(prefix="/api/contact-messages", tags=["contact"])


@router.post("", response_model=ContactMessageOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def submit_message(request: Request, payload: ContactMessageCreate, db: Session = Depends(get_db)):
    message = ContactMessage(**payload.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
