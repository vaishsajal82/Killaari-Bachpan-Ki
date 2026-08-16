"""
seed.py — populates the database with the real, publicly-available content
pulled from kilkaari.org.in, so the admin dashboard and public API aren't
empty on first run. Safe to re-run: skips anything that already exists.

Usage:
    python seed.py
"""

from app.database import Base, SessionLocal, engine
from app.models import Center, Program, StudentStory

PROGRAMS = [
    dict(
        title="Education",
        slug="education",
        summary="Bridge-learning and mainstream school enrolment for disadvantaged children.",
        description=(
            "Kilkaari brings children up to the right learning level first, "
            "then helps enrol them in the class they're actually ready for — "
            "supplying copybooks, pencils and pens along the way, and staying "
            "in touch with parents so support for a child's schooling doesn't fade."
        ),
        icon="fa-solid fa-graduation-cap",
        display_order=1,
    ),
]

CENTERS = [
    dict(name="Abdul Kalam Center", address="Near Mange Ram Park, Delhi – 110085", is_active=True),
    dict(name="Bhagat Singh Center", address="Sector-24, Rohini, Delhi – 110085", is_active=False),
    dict(name="Ram Prasad Bismil Center", address="Deep Vihar, Near Sector-24, Rohini, Delhi – 110085", is_active=False),
    dict(name="Sukhdev Center", address="Surya Vihar, near Kapasheda border, Haryana – 122006", is_active=True),
    dict(name="Chandra Shekhar Azaad Center", address="Near Wave City Center metro, Uttar Pradesh – 201307", is_active=False),
]

STUDENT_STORIES = [
    dict(name="Shivam", story_url="https://www.facebook.com/kilkaari.bachpanki/photos/a.372650456190535.1073741828.371765202945727/688952594560318/?type=1"),
    dict(name="Bharti", story_url="https://www.facebook.com/kilkaari.bachpanki/photos/a.372650456190535.1073741828.371765202945727/675343429254568/?type=1"),
    dict(name="Rajender", story_url="https://www.facebook.com/kilkaari.bachpanki/photos/a.372650456190535.1073741828.371765202945727/669911726464405/?type=1"),
    dict(name="Avantika", story_url="https://www.facebook.com/kilkaari.bachpanki/photos/a.372650456190535.1073741828.371765202945727/742233085898935/?type=1"),
]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(Program).first():
            for row in PROGRAMS:
                db.add(Program(**row))
            print(f"Seeded {len(PROGRAMS)} program(s).")

        if not db.query(Center).first():
            for row in CENTERS:
                db.add(Center(**row))
            print(f"Seeded {len(CENTERS)} center(s).")

        if not db.query(StudentStory).first():
            for row in STUDENT_STORIES:
                db.add(StudentStory(**row))
            print(f"Seeded {len(STUDENT_STORIES)} student stor(y/ies).")

        db.commit()
        print("Seeding complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
