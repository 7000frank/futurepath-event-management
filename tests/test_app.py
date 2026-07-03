import tempfile
import unittest
from datetime import date, time
from decimal import Decimal
from pathlib import Path

from werkzeug.security import generate_password_hash

from futurepath import create_app, db
from futurepath.models import Booking, Category, Comment, Event, User


class FuturePathTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test.sqlite"
        upload_path = Path(self.temp_dir.name) / "uploads"
        self.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
                "UPLOAD_FOLDER": str(upload_path),
                "PROPAGATE_EXCEPTIONS": False,
            }
        )

        @self.app.route("/_test-server-error")
        def test_server_error():
            raise RuntimeError("Deliberate test error")

        with self.app.app_context():
            db.drop_all()
            db.create_all()
            campus = Category(name="Campus Open Day", slug="campus-open-day")
            guidance = Category(name="Application Guidance", slug="application-guidance")
            owner = User(
                first_name="Owner",
                last_name="User",
                email="owner@example.com",
                password_hash=generate_password_hash("TestPass123!"),
                contact_number="0400000001",
                role="teacher",
            )
            member = User(
                first_name="Member",
                last_name="User",
                email="member@example.com",
                password_hash=generate_password_hash("TestPass123!"),
                contact_number="0400000002",
                role="student",
            )
            db.session.add_all([campus, guidance, owner, member])
            db.session.flush()
            event = Event(
                title="Test Campus Open Day",
                summary="A complete test summary for the FuturePath event workflow.",
                description="This description is deliberately long enough to satisfy the event form validation requirements during automated tests.",
                image_filename="nanjing-university-campus.jpg",
                event_date=date(2099, 7, 12),
                start_time=time(9, 0),
                end_time=time(12, 0),
                venue="Test Campus",
                presenter="Test Presenter",
                capacity=2,
                price=Decimal("0.00"),
                min_score=500,
                max_score=750,
                owner=owner,
                category=campus,
            )
            db.session.add(event)
            db.session.commit()
            self.event_id = event.id
            self.owner_id = owner.id
            self.member_id = member.id
            self.campus_id = campus.id
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.temp_dir.cleanup()

    def login(self, email="member@example.com", password="TestPass123!"):
        return self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

    def test_home_search_category_and_score_finder(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Campus Open Day", response.data)

        response = self.client.get("/?q=Campus&category=campus-open-day")
        self.assertIn(b"Test Campus Open Day", response.data)

        response = self.client.get("/?q=NoSuchEvent")
        self.assertIn(b"No matching events", response.data)

        response = self.client.get("/score-finder?score=650")
        self.assertIn(b"Test Campus Open Day", response.data)
        response = self.client.get("/score-finder?score=200")
        self.assertNotIn(b"Test Campus Open Day", response.data)

        with self.app.app_context():
            event = db.session.get(Event, self.event_id)
            event.event_date = date(2020, 1, 1)
            db.session.commit()
        response = self.client.get("/score-finder?score=650")
        self.assertNotIn(b"Test Campus Open Day", response.data)

    def test_register_login_and_logout(self):
        response = self.client.post(
            "/register",
            data={
                "first_name": "New",
                "last_name": "Student",
                "email": "new@example.com",
                "contact_number": "0400000003",
                "role": "student",
                "password": "NewPass123!",
                "confirm": "NewPass123!",
            },
            follow_redirects=True,
        )
        self.assertIn(b"account has been created", response.data)
        with self.app.app_context():
            user = db.session.scalar(db.select(User).where(User.email == "new@example.com"))
            self.assertIsNotNone(user)
            self.assertEqual(user.role, "student")

        response = self.login("new@example.com", "NewPass123!")
        self.assertIn(b"Welcome back, New", response.data)
        response = self.client.post("/logout", follow_redirects=True)
        self.assertIn(b"logged out", response.data)

    def test_teacher_registration_enables_event_creation(self):
        response = self.client.post(
            "/register",
            data={
                "first_name": "New",
                "last_name": "Teacher",
                "email": "newteacher@example.com",
                "contact_number": "0400000004",
                "role": "teacher",
                "password": "NewPass123!",
                "confirm": "NewPass123!",
            },
            follow_redirects=True,
        )
        self.assertIn(b"account has been created", response.data)
        self.login("newteacher@example.com", "NewPass123!")
        response = self.client.get("/events/create")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Create a Nonprofit Event", response.data)
        with self.app.app_context():
            teacher = db.session.scalar(db.select(User).where(User.email == "newteacher@example.com"))
            self.assertEqual(teacher.role, "teacher")

    def test_booking_is_one_person_and_duplicate_is_rejected(self):
        response = self.client.post(f"/events/{self.event_id}/book")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        self.login()
        response = self.client.post(f"/events/{self.event_id}/book")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith(f"/events/{self.event_id}"))

        response = self.client.get(response.headers["Location"], follow_redirects=True)
        self.assertIn(b"Booking confirmed", response.data)
        self.assertIn(b"Already Booked", response.data)

        response = self.client.post(
            f"/events/{self.event_id}/book",
            follow_redirects=True,
        )
        self.assertIn(b"already booked this event", response.data)
        self.assertIn(b"Already Booked", response.data)

        with self.app.app_context():
            booking = db.session.scalar(db.select(Booking))
            event = db.session.get(Event, self.event_id)
            self.assertTrue(booking.reference.startswith("FP"))
            self.assertEqual(booking.quantity, 1)
            self.assertEqual(db.session.scalar(db.select(db.func.count(Booking.id))), 1)
            self.assertEqual(event.remaining_places, 1)
            self.assertEqual(event.status, "Open")

    def test_event_becomes_sold_out_when_last_place_is_booked(self):
        with self.app.app_context():
            db.session.get(Event, self.event_id).capacity = 1
            db.session.commit()
        self.login()
        self.client.post(f"/events/{self.event_id}/book")
        with self.app.app_context():
            event = db.session.get(Event, self.event_id)
            self.assertEqual(event.remaining_places, 0)
            self.assertEqual(event.status, "Sold Out")

    def test_cancelling_booking_preserves_history_and_releases_places(self):
        self.login()
        self.client.post(f"/events/{self.event_id}/book")
        with self.app.app_context():
            booking_id = db.session.scalar(db.select(Booking.id))
            first_reference = db.session.get(Booking, booking_id).reference

        response = self.client.post(
            f"/bookings/{booking_id}/cancel",
            follow_redirects=True,
        )
        self.assertIn(b"has been cancelled and 1 place(s) released", response.data)
        self.assertIn(b"Cancelled", response.data)

        with self.app.app_context():
            booking = db.session.get(Booking, booking_id)
            event = db.session.get(Event, self.event_id)
            self.assertIsNotNone(booking.cancelled_at)
            self.assertEqual(booking.status, "Cancelled")
            self.assertEqual(event.remaining_places, 2)
            self.assertEqual(event.status, "Open")

        response = self.client.get(f"/events/{self.event_id}")
        self.assertIn(b"Book My Place", response.data)
        self.assertNotIn(b"Booking Cancelled", response.data)
        self.assertNotIn(b"Book Again", response.data)

        response = self.client.post(
            f"/events/{self.event_id}/book",
            follow_redirects=True,
        )
        self.assertIn(b"Booking confirmed", response.data)

        with self.app.app_context():
            booking = db.session.get(Booking, booking_id)
            event = db.session.get(Event, self.event_id)
            self.assertIsNone(booking.cancelled_at)
            self.assertNotEqual(booking.reference, first_reference)
            self.assertEqual(db.session.scalar(db.select(db.func.count(Booking.id))), 1)
            self.assertEqual(event.remaining_places, 1)

    def test_user_cannot_cancel_another_users_booking(self):
        self.login()
        self.client.post(f"/events/{self.event_id}/book")
        with self.app.app_context():
            booking_id = db.session.scalar(db.select(Booking.id))

        self.client.post("/logout")
        self.login("owner@example.com")
        response = self.client.post(f"/bookings/{booking_id}/cancel")
        self.assertEqual(response.status_code, 403)

    def test_booking_is_rejected_when_event_is_sold_out(self):
        with self.app.app_context():
            event = db.session.get(Event, self.event_id)
            event.capacity = 1
            owner = db.session.get(User, self.owner_id)
            db.session.add(
                Booking(
                    reference="FPTESTSOLDOUT",
                    quantity=1,
                    unit_price=Decimal("0.00"),
                    user=owner,
                    event=event,
                )
            )
            db.session.commit()
        self.login()
        response = self.client.post(f"/events/{self.event_id}/book", follow_redirects=True)
        self.assertIn(b"sold out and cannot accept bookings", response.data)
        with self.app.app_context():
            self.assertEqual(db.session.scalar(db.select(db.func.count(Booking.id))), 1)

    def test_comment_is_saved_and_visible(self):
        self.login()
        response = self.client.post(
            f"/events/{self.event_id}/comments",
            data={"body": "Will the event include a laboratory tour?"},
            follow_redirects=True,
        )
        self.assertIn(b"laboratory tour", response.data)
        with self.app.app_context():
            self.assertEqual(db.session.scalar(db.select(db.func.count(Comment.id))), 1)

    def test_only_creator_can_edit_or_cancel_event(self):
        self.login()
        response = self.client.get("/events/create")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/events/manage")
        self.assertEqual(response.status_code, 403)
        response = self.client.get(f"/events/{self.event_id}/delete")
        self.assertEqual(response.status_code, 403)
        response = self.client.get(f"/events/{self.event_id}/edit")
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Access Denied", response.data)

        self.client.post("/logout")
        self.login("owner@example.com")
        response = self.client.get("/events/manage")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Manage Events", response.data)
        self.assertIn(b"Test Campus Open Day", response.data)
        self.assertIn(b"Edit", response.data)
        response = self.client.get(f"/events/{self.event_id}/edit")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            f"/events/{self.event_id}/cancel",
            data={"return_to": "manage_events"},
            follow_redirects=True,
        )
        self.assertIn(b"event has been cancelled", response.data)
        self.assertIn(b"Event cancelled", response.data)
        with self.app.app_context():
            self.assertEqual(db.session.get(Event, self.event_id).status, "Cancelled")

        response = self.client.post(f"/events/{self.event_id}/delete", follow_redirects=True)
        self.assertIn(b"permanently deleted", response.data)
        with self.app.app_context():
            self.assertIsNone(db.session.get(Event, self.event_id))

    def test_event_with_booking_cannot_be_permanently_deleted(self):
        self.login()
        self.client.post(f"/events/{self.event_id}/book")
        self.client.post("/logout")
        self.login("owner@example.com")

        response = self.client.get(f"/events/{self.event_id}/delete")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Permanent deletion is unavailable", response.data)

        response = self.client.post(f"/events/{self.event_id}/delete", follow_redirects=True)
        self.assertIn(b"cannot be permanently deleted", response.data)
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Event, self.event_id))

    def test_creator_can_create_event_and_status_is_automatic(self):
        self.login("owner@example.com")
        response = self.client.post(
            "/events/create",
            data={
                "title": "New Guidance Workshop",
                "category_id": self.campus_id,
                "presenter": "FuturePath Team",
                "summary": "A sufficiently detailed summary for a new guidance workshop.",
                "description": "This is a sufficiently detailed description for a new guidance workshop created during an automated test.",
                "event_date": "2099-08-01",
                "start_time": "10:00",
                "end_time": "12:00",
                "venue": "FuturePath Hall",
                "capacity": "40",
                "price": "0.00",
                "min_score": "0",
                "max_score": "750",
            },
            follow_redirects=True,
        )
        self.assertIn(b"published with an Open status", response.data)
        self.assertIn(b"New Guidance Workshop", response.data)
        with self.app.app_context():
            event = db.session.scalar(db.select(Event).where(Event.title == "New Guidance Workshop"))
            self.assertEqual(event.owner_id, self.owner_id)
            self.assertEqual(event.status, "Open")
            self.assertEqual(event.price, Decimal("0.00"))

    def test_custom_404_and_500_pages(self):
        response = self.client.get("/missing-page")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page Not Found", response.data)

        response = self.client.get("/_test-server-error")
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Something Went Wrong", response.data)


if __name__ == "__main__":
    unittest.main()
