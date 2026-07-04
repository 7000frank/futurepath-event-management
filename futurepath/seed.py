from datetime import date, datetime, time
from decimal import Decimal

from werkzeug.security import generate_password_hash

from . import db
from .models import Booking, Category, Comment, Event, User


def seed_database():
    categories = {
        "campus": Category(name="Campus Open Day", slug="campus-open-day"),
        "guidance": Category(name="Application Guidance", slug="application-guidance"),
        "career": Category(name="Career Skills", slug="career-skills"),
        "research": Category(name="Research Discovery", slug="research-discovery"),
        "experience": Category(name="Subject Experience", slug="subject-experience"),
        "family": Category(name="Family Briefing", slug="family-briefing"),
    }
    db.session.add_all(categories.values())

    frank = User(
        first_name="Frank",
        last_name="Fan",
        email="frank@example.com",
        password_hash=generate_password_hash("FuturePath123!"),
        contact_number="13800000001",
        street_address="88 Xianlin Avenue, Nanjing",
        role="teacher",
    )
    chen = User(
        first_name="Chen",
        last_name="Demo",
        email="chen@example.com",
        password_hash=generate_password_hash("FuturePath123!"),
        contact_number="13800000002",
        street_address="16 Jiangjun Avenue, Nanjing",
        role="teacher",
    )
    student = User(
        first_name="Student",
        last_name="Demo",
        email="student@example.com",
        password_hash=generate_password_hash("FuturePath123!"),
        contact_number="13800000003",
        street_address="12 Student Road, Nanjing",
        role="student",
    )
    student_two = User(
        first_name="Second",
        last_name="Student",
        email="student.two@example.com",
        password_hash=generate_password_hash("FuturePath123!"),
        contact_number="13800000004",
        street_address="26 Learning Street, Nanjing",
        role="student",
    )
    db.session.add_all([frank, chen, student, student_two])
    db.session.flush()

    event_data = [
        dict(
            key="nanjing",
            title="Nanjing University Open Day: Xianlin Campus Discovery",
            summary="Explore academic spaces, student life and application questions through an unofficial nonprofit course demonstration.",
            description="Visit teaching buildings, shared learning spaces and key areas of Nanjing University's Xianlin Campus. Volunteer guides introduce the study environment and help students prepare useful questions before attending a real university open day.",
            image_filename="nanjing-university-campus.jpg",
            event_date=date(2026, 7, 12),
            start_time=time(9, 0),
            end_time=time(12, 0),
            venue="Xianlin Campus, Nanjing",
            presenter="FuturePath Volunteer Guides",
            capacity=60,
            min_score=600,
            max_score=750,
            category=categories["campus"],
            owner=frank,
        ),
        dict(
            key="jinling",
            title="Jinling Institute of Technology: Jiangning Campus Open Day",
            summary="Discover applied degree pathways, teaching spaces and student support at a practical campus visit.",
            description="This open day introduces applied degree subjects, laboratories, learning support and student life at the Jiangning campus. The event is an unofficial course demonstration and is not organised by the institution shown.",
            image_filename="jinling-institute-campus.jpg",
            event_date=date(2026, 7, 15),
            start_time=time(9, 0),
            end_time=time(12, 30),
            venue="Jiangning Campus, Nanjing",
            presenter="FuturePath Campus Volunteers",
            capacity=45,
            min_score=450,
            max_score=599,
            category=categories["campus"],
            owner=chen,
        ),
        dict(
            key="qut",
            title="QUT Open Day: Gardens Point Campus Experience",
            summary="A Brisbane campus discovery event covering technology, design and international study pathways.",
            description="Participants explore the Gardens Point campus and review technology, engineering, design and international study information. This is an unofficial FuturePath course demonstration, not an event endorsed by QUT.",
            image_filename="qut-gardens-point-campus.jpg",
            event_date=date(2026, 8, 1),
            start_time=time(10, 0),
            end_time=time(14, 0),
            venue="Gardens Point Campus, Brisbane",
            presenter="FuturePath International Guides",
            capacity=80,
            min_score=500,
            max_score=750,
            category=categories["campus"],
            owner=frank,
        ),
        dict(
            key="xuefeng",
            title="Zhang Xuefeng-Style Gaokao Application Strategy Lecture",
            summary="A direct and practical examination of score, ranking, university choice, degree subjects and career outcomes.",
            description="This free lecture uses an evidence-focused format to explain how applicants can compare provincial rank, university location, degree curriculum and employment pathways. The public-figure reference is stylistic course-demo inspiration only and does not imply affiliation or attendance.",
            image_filename="zhang-xuefeng-guidance-poster.jpg",
            event_date=date(2026, 7, 18),
            start_time=time(19, 30),
            end_time=time(21, 30),
            venue="FuturePath Live Studio (online demo)",
            presenter="FuturePath Volunteer Advisers",
            capacity=150,
            min_score=0,
            max_score=750,
            category=categories["guidance"],
            owner=frank,
        ),
        dict(
            key="liwenya",
            title="Li Wenya Institute for Advanced Scientific Research Open Day",
            summary="An introduction to disciplined observation, evidence-based inquiry and interdisciplinary scientific thinking.",
            description="The fictional Li Wenya Institute presents a structured introduction to observation, measurement, research ethics and interdisciplinary reasoning. This institute exists only within this course demonstration.",
            image_filename="li-wenya-research-institute.jpg",
            event_date=date(2026, 7, 20),
            start_time=time(10, 0),
            end_time=time(12, 30),
            venue="Future Science Research Hall (fictional demo)",
            presenter="FuturePath Volunteer Guides",
            capacity=200,
            min_score=0,
            max_score=449,
            category=categories["research"],
            owner=chen,
        ),
        dict(
            key="gazi",
            title="Gazi-Style Livestream Commerce Skills Lecture",
            summary="A practical introduction to product communication, consumer trust and responsible livestream commerce.",
            description="This fictional course demonstration examines presentation planning, product evidence, consumer protection and responsible livestream practice. The stylistic reference does not imply affiliation or attendance.",
            image_filename="gazi-livestream-commerce.jpg",
            event_date=date(2026, 7, 22),
            start_time=time(19, 0),
            end_time=time(21, 0),
            venue="FuturePath Skills Studio (fictional demo)",
            presenter="FuturePath Career Volunteers",
            capacity=180,
            min_score=0,
            max_score=449,
            category=categories["career"],
            owner=chen,
        ),
        dict(
            key="southeast",
            title="Southeast University Open Day: Engineering Lab Route",
            summary="A focused engineering route through laboratories, project spaces and degree-planning information.",
            description="This unofficial demonstration visit presents an engineering-focused campus route and introduces questions students can ask about laboratory learning and industry projects.",
            image_filename="southeast-university-campus.jpg",
            event_date=date(2026, 7, 13),
            start_time=time(9, 30),
            end_time=time(12, 0),
            venue="Jiulonghu Campus (course demo)",
            presenter="FuturePath Engineering Volunteers",
            capacity=2,
            min_score=600,
            max_score=750,
            category=categories["campus"],
            owner=chen,
        ),
        dict(
            key="past",
            title="Subject Experience Day: What You Will Actually Study",
            summary="A completed subject workshop retained to demonstrate an automatically inactive event.",
            description="Students compared the first-year curriculum of computing, finance, law and health degrees. This completed record demonstrates how past event dates automatically produce an Inactive status.",
            image_filename="major-workshop.png",
            event_date=date(2026, 6, 22),
            start_time=time(19, 0),
            end_time=time(20, 30),
            venue="FuturePath Online Classroom",
            presenter="FuturePath Subject Volunteers",
            capacity=120,
            min_score=0,
            max_score=750,
            category=categories["experience"],
            owner=frank,
        ),
        dict(
            key="cancelled",
            title="Family Briefing: Understanding Application Timelines",
            summary="A cancelled demonstration event explaining key application dates and family support responsibilities.",
            description="This record demonstrates a Cancelled state. The session would have explained application milestones, document preparation and how families can support independent student decisions.",
            image_filename="futurepath-hero.jpg",
            event_date=date(2026, 7, 25),
            start_time=time(14, 0),
            end_time=time(15, 30),
            venue="FuturePath Community Room",
            presenter="FuturePath Family Volunteers",
            capacity=90,
            min_score=0,
            max_score=750,
            category=categories["family"],
            owner=frank,
            cancelled=True,
        ),
    ]

    events = {}
    for data in event_data:
        key = data.pop("key")
        events[key] = Event(price=Decimal("0.00"), **data)
        db.session.add(events[key])
    db.session.flush()

    db.session.add_all(
        [
            Booking(
                reference="FP202607050018",
                quantity=1,
                unit_price=Decimal("0.00"),
                booked_at=datetime(2026, 6, 29, 18, 42),
                user=student,
                event=events["xuefeng"],
            ),
            Booking(
                reference="FP202607080007",
                quantity=1,
                unit_price=Decimal("0.00"),
                booked_at=datetime(2026, 6, 26, 10, 18),
                user=student,
                event=events["nanjing"],
            ),
            Booking(
                reference="FP202607010002",
                quantity=1,
                unit_price=Decimal("0.00"),
                booked_at=datetime(2026, 7, 1, 9, 0),
                user=student,
                event=events["southeast"],
            ),
            Booking(
                reference="FP202607010003",
                quantity=1,
                unit_price=Decimal("0.00"),
                booked_at=datetime(2026, 7, 1, 9, 5),
                user=student_two,
                event=events["southeast"],
            ),
            Booking(
                reference="FP202606180031",
                quantity=1,
                unit_price=Decimal("0.00"),
                booked_at=datetime(2026, 6, 18, 21, 6),
                user=student,
                event=events["past"],
            ),
            Comment(
                body="The schedule and campus location are very clear. Will the tour include teaching laboratories?",
                posted_at=datetime(2026, 6, 28, 12, 30),
                user=student,
                event=events["nanjing"],
            ),
            Comment(
                body="I appreciated the explanation of curriculum and career outcomes.",
                posted_at=datetime(2026, 6, 29, 20, 15),
                user=student,
                event=events["xuefeng"],
            ),
        ]
    )
    db.session.commit()
