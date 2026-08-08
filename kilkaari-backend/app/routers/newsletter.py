from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NewsletterSubscriber
from app.schemas import NewsletterSubscribeIn, NewsletterSubscriberOut

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])


@router.post("/subscribe", response_model=NewsletterSubscriberOut, status_code=status.HTTP_201_CREATED)
def subscribe(payload: NewsletterSubscribeIn, db: Session = Depends(get_db)):
    existing = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == payload.email).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
        return existing

    subscriber = NewsletterSubscriber(email=payload.email)
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber


@router.post("/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(payload: NewsletterSubscribeIn, db: Session = Depends(get_db)):
    existing = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == payload.email).first()
    if existing:
        existing.is_active = False
        db.commit()
    return None
