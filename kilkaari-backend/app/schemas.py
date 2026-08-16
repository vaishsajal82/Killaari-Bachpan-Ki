"""
schemas.py — Pydantic models used for request validation and API responses.
"""

from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

from app.models import UserRole, DonationStatus, DonationType, ApplicationStatus


def _validate_image_url(value: Optional[str]) -> Optional[str]:
    """Catch the #1 real-world mistake: pasting a share/preview link
    (Google Drive, Dropbox, a Pinterest pin, etc.) instead of a direct
    link that resolves straight to an image file. This can't guarantee
    the URL is a *working* image (that needs an actual request), but it
    rejects obviously-wrong input immediately instead of silently saving
    a URL that will never render on the public site. Shared by every
    content type with an image field (programs, events, campaigns,
    gallery, testimonials, student stories) so the same mistake is
    caught everywhere, not just in one place.
    """
    if value is None or value == "":
        return value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("image_url must be a full http(s) URL, e.g. https://example.com/photo.jpg")
    known_share_hosts = ("drive.google.com", "dropbox.com", "www.dropbox.com", "pinterest.com", "www.pinterest.com")
    is_drive = "drive.google.com" in parsed.netloc
    drive_ok = ("/uc?" in value) or ("/thumbnail?" in value)
    if any(host in parsed.netloc for host in known_share_hosts) and not (is_drive and drive_ok):
        raise ValueError(
            "This looks like a share/preview link, not a direct image link. "
            "Google Drive/Dropbox/Pinterest links usually won't render as images — "
            "use a direct-image host (e.g. Cloudinary, Imgur, S3) or a direct-download link instead."
        )
    return value


# ---------------------------------------------------------------------------
# Auth / Users
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------------------
# Donations
# ---------------------------------------------------------------------------

class DonationCreate(BaseModel):
    donor_name: str
    donor_email: EmailStr
    donor_phone: Optional[str] = None
    amount: float
    donation_type: DonationType = DonationType.one_time
    campaign_id: Optional[str] = None


class DonationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    donor_name: str
    donor_email: EmailStr
    amount: float
    currency: str
    donation_type: DonationType
    campaign_id: Optional[str] = None
    status: DonationStatus
    payment_provider: Optional[str] = None
    provider_reference: Optional[str] = None
    created_at: datetime


class DonationInitResponse(BaseModel):
    """Returned right after a donation record is created, before payment
    is completed. `checkout` carries whatever the active payment provider
    needs on the frontend to open its checkout (redirect URL for a real
    gateway, or a mock payload in test mode)."""
    donation: DonationOut
    checkout: dict


# ---------------------------------------------------------------------------
# Volunteer applications
# ---------------------------------------------------------------------------

class VolunteerApplicationCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    city: Optional[str] = None
    area_of_interest: Optional[str] = None
    availability: Optional[str] = None
    message: Optional[str] = None


class VolunteerApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    email: EmailStr
    phone: str
    city: Optional[str] = None
    area_of_interest: Optional[str] = None
    availability: Optional[str] = None
    message: Optional[str] = None
    status: ApplicationStatus
    created_at: datetime


class VolunteerApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

class ContactMessageCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    comment: str


class ContactMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    comment: str
    is_read: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

class NewsletterSubscribeIn(BaseModel):
    email: EmailStr


class NewsletterSubscriberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    subscribed_at: datetime
    is_active: bool


# ---------------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------------

class ProgramBase(BaseModel):
    title: str
    slug: str
    summary: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    display_order: int = 0
    is_published: bool = True

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_published: Optional[bool] = None

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)


class ProgramOut(ProgramBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

EVENT_STATUSES = ("upcoming", "completed", "postponed")


def _validate_event_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    if value not in EVENT_STATUSES:
        raise ValueError(f"status must be one of {EVENT_STATUSES}")
    return value


def _validate_http_url(value: Optional[str]) -> Optional[str]:
    """For links that are clicked, not displayed as images (e.g. an event's
    registration_url) — rejects anything that isn't a plain http(s) link.
    Without this, a value like "javascript:alert(document.cookie)" would
    pass straight through: it contains no HTML-special characters, so
    output-side HTML escaping does nothing to stop it, and clicking the
    resulting <a href="javascript:..."> link would execute it. HTML
    escaping and URL-scheme validation guard against different things —
    this project needs both, not just one.
    """
    if value is None or value == "":
        return value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("must be a full http(s) URL, e.g. https://example.com/register")
    return value


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    event_date: datetime
    image_url: Optional[str] = None
    registration_url: Optional[str] = None
    is_published: bool = True
    status: str = "upcoming"

    @field_validator("status")
    @classmethod
    def check_status(cls, v):
        return _validate_event_status(v)

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)

    @field_validator("registration_url")
    @classmethod
    def check_registration_url(cls, v):
        return _validate_http_url(v)


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    event_date: Optional[datetime] = None
    image_url: Optional[str] = None
    registration_url: Optional[str] = None
    is_published: Optional[bool] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def check_status(cls, v):
        return _validate_event_status(v)

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)

    @field_validator("registration_url")
    @classmethod
    def check_registration_url(cls, v):
        return _validate_http_url(v)


class EventOut(EventBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

class CampaignBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    goal_amount: float
    is_active: bool = True

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    goal_amount: Optional[float] = None
    is_active: Optional[bool] = None

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)


class CampaignOut(CampaignBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    raised_amount: float


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------

class GalleryItemBase(BaseModel):
    title: Optional[str] = None
    image_url: str
    category: Optional[str] = None
    caption: Optional[str] = None
    display_order: int = 0
    # Internal bookkeeping only, not admin-facing — the admin portal's
    # upload flow sets this automatically from the Cloudinary upload
    # response so the backend can clean up the old asset on
    # replace/delete. Never required: a manually-pasted external URL
    # (not from the upload button) simply leaves this null, which is
    # fine — cleanup is just skipped for those.
    cloudinary_public_id: Optional[str] = None

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)


class GalleryItemCreate(GalleryItemBase):
    pass


class GalleryItemUpdate(BaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    caption: Optional[str] = None
    display_order: Optional[int] = None
    cloudinary_public_id: Optional[str] = None

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)


class GalleryItemOut(GalleryItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ---------------------------------------------------------------------------
# Testimonials
# ---------------------------------------------------------------------------

class TestimonialBase(BaseModel):
    name: str
    role: Optional[str] = None
    quote: str
    avatar_url: Optional[str] = None
    is_published: bool = True

    @field_validator("avatar_url")
    @classmethod
    def check_avatar_url(cls, v):
        return _validate_image_url(v)


class TestimonialCreate(TestimonialBase):
    pass


class TestimonialUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    quote: Optional[str] = None
    avatar_url: Optional[str] = None
    is_published: Optional[bool] = None

    @field_validator("avatar_url")
    @classmethod
    def check_avatar_url(cls, v):
        return _validate_image_url(v)


class TestimonialOut(TestimonialBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ---------------------------------------------------------------------------
# Centers
# ---------------------------------------------------------------------------

class CenterBase(BaseModel):
    name: str
    address: str
    map_url: Optional[str] = None
    is_active: bool = True


class CenterCreate(CenterBase):
    pass


class CenterUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    map_url: Optional[str] = None
    is_active: Optional[bool] = None


class CenterOut(CenterBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ---------------------------------------------------------------------------
# Student stories
# ---------------------------------------------------------------------------

class StudentStoryBase(BaseModel):
    name: str
    story_url: Optional[str] = None
    image_url: Optional[str] = None
    is_published: bool = True

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)

    @field_validator("story_url")
    @classmethod
    def check_story_url(cls, v):
        return _validate_http_url(v)


class StudentStoryCreate(StudentStoryBase):
    pass


class StudentStoryUpdate(BaseModel):
    name: Optional[str] = None
    story_url: Optional[str] = None
    image_url: Optional[str] = None
    is_published: Optional[bool] = None

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v):
        return _validate_image_url(v)

    @field_validator("story_url")
    @classmethod
    def check_story_url(cls, v):
        return _validate_http_url(v)


class StudentStoryOut(StudentStoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ---------------------------------------------------------------------------
# Admin dashboard summary
# ---------------------------------------------------------------------------

class DashboardSummary(BaseModel):
    total_donations_amount: float
    total_donations_count: int
    successful_donations_count: int
    pending_volunteer_applications: int
    unread_contact_messages: int
    newsletter_subscribers: int
    active_campaigns: int
