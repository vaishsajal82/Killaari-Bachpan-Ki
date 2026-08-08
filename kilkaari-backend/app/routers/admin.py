from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import (
    Campaign, ContactMessage, Donation, DonationStatus, NewsletterSubscriber,
    User, VolunteerApplication, ApplicationStatus,
)
from app.schemas import (
    ContactMessageOut, DashboardSummary, DonationOut, UserOut,
    VolunteerApplicationOut, VolunteerApplicationStatusUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db)):
    total_amount = db.query(func.coalesce(func.sum(Donation.amount), 0.0)).filter(
        Donation.status == DonationStatus.success
    ).scalar()

    return DashboardSummary(
        total_donations_amount=float(total_amount or 0),
        total_donations_count=db.query(Donation).count(),
        successful_donations_count=db.query(Donation).filter(Donation.status == DonationStatus.success).count(),
        pending_volunteer_applications=db.query(VolunteerApplication).filter(
            VolunteerApplication.status == ApplicationStatus.new
        ).count(),
        unread_contact_messages=db.query(ContactMessage).filter(ContactMessage.is_read == False).count(),  # noqa: E712
        newsletter_subscribers=db.query(NewsletterSubscriber).filter(NewsletterSubscriber.is_active == True).count(),  # noqa: E712
        active_campaigns=db.query(Campaign).filter(Campaign.is_active == True).count(),  # noqa: E712
    )


# ---------------------------------------------------------------------------
# Donations oversight
# ---------------------------------------------------------------------------

@router.get("/donations", response_model=List[DonationOut])
def list_all_donations(db: Session = Depends(get_db)):
    return db.query(Donation).order_by(Donation.created_at.desc()).all()


# ---------------------------------------------------------------------------
# Volunteer applications
# ---------------------------------------------------------------------------

@router.get("/volunteer-applications", response_model=List[VolunteerApplicationOut])
def list_applications(db: Session = Depends(get_db)):
    return db.query(VolunteerApplication).order_by(VolunteerApplication.created_at.desc()).all()


@router.patch("/volunteer-applications/{application_id}", response_model=VolunteerApplicationOut)
def update_application_status(
    application_id: str, payload: VolunteerApplicationStatusUpdate, db: Session = Depends(get_db)
):
    application = db.query(VolunteerApplication).filter(VolunteerApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = payload.status
    db.commit()
    db.refresh(application)
    return application


# ---------------------------------------------------------------------------
# Contact messages
# ---------------------------------------------------------------------------

@router.get("/contact-messages", response_model=List[ContactMessageOut])
def list_messages(db: Session = Depends(get_db)):
    return db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()


@router.patch("/contact-messages/{message_id}/mark-read", response_model=ContactMessageOut)
def mark_message_read(message_id: str, db: Session = Depends(get_db)):
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.is_read = True
    db.commit()
    db.refresh(message)
    return message


# ---------------------------------------------------------------------------
# User accounts
# ---------------------------------------------------------------------------

@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
