from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContactMessage
from app.schemas import ContactMessageCreate, ContactMessageOut

router = APIRouter(prefix="/api/contact-messages", tags=["contact"])


@router.post("", response_model=ContactMessageOut, status_code=status.HTTP_201_CREATED)
def submit_message(payload: ContactMessageCreate, db: Session = Depends(get_db)):
    message = ContactMessage(**payload.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
