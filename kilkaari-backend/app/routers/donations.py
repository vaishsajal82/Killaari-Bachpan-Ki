from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user, oauth2_scheme
from app.config import settings
from app.database import get_db
from app.models import Campaign, Donation, DonationStatus, User
from app.payments import get_payment_provider
from app.rate_limit import limiter
from app.schemas import DonationCreate, DonationInitResponse, DonationOut

router = APIRouter(prefix="/api/donations", tags=["donations"])


def _try_get_current_user(token: Optional[str], db: Session) -> Optional[User]:
    """Donations are allowed as a guest. If a bearer token is present and
    valid, we attach the donation to that account; otherwise it's anonymous."""
    if not token:
        return None
    try:
        from app.auth import get_current_user as _gcu
        # Reuse the same decoding logic without forcing a 401 for guests.
        from jose import jwt
        from app.config import settings

        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        return db.query(User).filter(User.id == user_id).first() if user_id else None
    except Exception:
        return None


@router.post("", response_model=DonationInitResponse, status_code=201)
@limiter.limit("10/minute")
def create_donation(
    request: Request,
    payload: DonationCreate,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Donation amount must be greater than zero")

    campaign = None
    if payload.campaign_id:
        campaign = db.query(Campaign).filter(Campaign.id == payload.campaign_id).first()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

    user = _try_get_current_user(token, db)

    donation = Donation(
        user_id=user.id if user else None,
        donor_name=payload.donor_name,
        donor_email=payload.donor_email,
        donor_phone=payload.donor_phone,
        amount=payload.amount,
        donation_type=payload.donation_type,
        campaign_id=payload.campaign_id,
        status=DonationStatus.pending,
    )
    db.add(donation)
    db.commit()
    db.refresh(donation)

    provider = get_payment_provider()
    checkout = provider.create_checkout(donation)

    donation.payment_provider = checkout.get("provider")
    donation.provider_reference = checkout.get("reference")
    db.commit()
    db.refresh(donation)

    return DonationInitResponse(donation=DonationOut.model_validate(donation), checkout=checkout)


@router.post("/{donation_id}/confirm-test-payment", response_model=DonationOut)
def confirm_test_payment(donation_id: str, db: Session = Depends(get_db)):
    """Only meaningful when PAYMENT_PROVIDER=test. Marks a pending donation
    as successful and, if tied to a campaign, adds the amount to its
    raised_amount — so the whole flow can be demoed without a real gateway.

    Deliberately gated on the server's actual configured payment_provider
    (not just left to the docstring/frontend to respect): without this
    check, this endpoint would let anyone mark ANY donation ID as
    successful with a single unauthenticated request — in production, that
    means fabricating "paid" donations and inflating campaign totals with
    no payment ever having happened. Returning 404 here in any real
    (non-test) environment means the endpoint is a guaranteed no-op unless
    the deployment has explicitly opted into test mode.
    """
    if settings.payment_provider != "test":
        raise HTTPException(status_code=404, detail="Not found")

    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    if donation.status == DonationStatus.success:
        return donation

    donation.status = DonationStatus.success
    if donation.campaign_id:
        campaign = db.query(Campaign).filter(Campaign.id == donation.campaign_id).first()
        if campaign:
            campaign.raised_amount = (campaign.raised_amount or 0) + donation.amount

    db.commit()
    db.refresh(donation)
    return donation


@router.get("/me", response_model=List[DonationOut])
def my_donations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Donation).filter(Donation.user_id == current_user.id).order_by(Donation.created_at.desc()).all()
