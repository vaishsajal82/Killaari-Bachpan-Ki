"""
models.py — SQLAlchemy ORM models for the Kilkaari backend.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Users & auth
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    admin = "admin"
    volunteer = "volunteer"
    donor = "donor"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String(150), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.donor, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    donations = relationship("Donation", back_populates="user")


# ---------------------------------------------------------------------------
# Donations
# ---------------------------------------------------------------------------

class DonationStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


class DonationType(str, enum.Enum):
    one_time = "one_time"
    monthly_child_sponsorship = "monthly_child_sponsorship"


class Donation(Base):
    __tablename__ = "donations"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # null = guest donation

    donor_name = Column(String(150), nullable=False)
    donor_email = Column(String(200), nullable=False)
    donor_phone = Column(String(20), nullable=True)

    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR")
    donation_type = Column(Enum(DonationType), default=DonationType.one_time)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True)

    status = Column(Enum(DonationStatus), default=DonationStatus.pending)
    payment_provider = Column(String(30), nullable=True)
    provider_reference = Column(String(200), nullable=True)  # gateway order/txn id

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="donations")
    campaign = relationship("Campaign", back_populates="donations")


# ---------------------------------------------------------------------------
# Volunteer applications
# ---------------------------------------------------------------------------

class ApplicationStatus(str, enum.Enum):
    new = "new"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"


class VolunteerApplication(Base):
    __tablename__ = "volunteer_applications"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String(150), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    city = Column(String(100), nullable=True)
    area_of_interest = Column(String(150), nullable=True)  # e.g. "Teach & Mentor"
    availability = Column(String(150), nullable=True)      # e.g. "Weekends"
    message = Column(Text, nullable=True)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.new)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Contact messages
# ---------------------------------------------------------------------------

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String(150), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    comment = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String(200), unique=True, nullable=False)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


# ---------------------------------------------------------------------------
# Content managed by the admin panel
# ---------------------------------------------------------------------------

class Program(Base):
    __tablename__ = "programs"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(150), nullable=False)
    slug = Column(String(150), unique=True, nullable=False)
    summary = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)   # e.g. font-awesome class
    image_url = Column(String(300), nullable=True)
    display_order = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    event_date = Column(DateTime, nullable=False)
    image_url = Column(String(300), nullable=True)
    registration_url = Column(String(300), nullable=True)
    is_published = Column(Boolean, default=True)
    # "upcoming" | "completed" | "postponed" — set by admin, drives what the
    # public Events page shows (see routers/events.py + Kilkaari/assets/js/events.js)
    status = Column(String(20), default="upcoming", nullable=False)


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(300), nullable=True)
    goal_amount = Column(Float, nullable=False)
    raised_amount = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    donations = relationship("Donation", back_populates="campaign")


class GalleryItem(Base):
    __tablename__ = "gallery_items"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(200), nullable=True)
    image_url = Column(String(300), nullable=False)
    category = Column(String(100), nullable=True)  # e.g. "education", "health"
    caption = Column(String(300), nullable=True)
    display_order = Column(Integer, default=0)


class Testimonial(Base):
    __tablename__ = "testimonials"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(150), nullable=False)
    role = Column(String(100), nullable=True)  # e.g. "Parent", "Volunteer"
    quote = Column(Text, nullable=False)
    avatar_url = Column(String(300), nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Center(Base):
    __tablename__ = "centers"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(150), nullable=False)
    address = Column(String(300), nullable=False)
    map_url = Column(String(300), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StudentStory(Base):
    __tablename__ = "student_stories"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(150), nullable=False)
    story_url = Column(String(300), nullable=True)
    image_url = Column(String(300), nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
