from datetime import date, datetime
from decimal import Decimal

from flask_login import UserMixin

from . import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(30), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    events = db.relationship("Event", back_populates="owner", cascade="all, delete-orphan")
    bookings = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_teacher(self):
        return self.role == "teacher"

    @property
    def role_label(self):
        return "Teacher" if self.is_teacher else "Student"


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)

    events = db.relationship("Event", back_populates="category")


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    summary = db.Column(db.String(260), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False, default="futurepath-hero.jpg")
    image_is_upload = db.Column(db.Boolean, nullable=False, default=False)
    event_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    venue = db.Column(db.String(180), nullable=False)
    presenter = db.Column(db.String(140), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(8, 2), nullable=False, default=Decimal("0.00"))
    min_score = db.Column(db.Integer, nullable=False, default=0)
    max_score = db.Column(db.Integer, nullable=False, default=750)
    cancelled = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)

    owner = db.relationship("User", back_populates="events")
    category = db.relationship("Category", back_populates="events")
    bookings = db.relationship("Booking", back_populates="event", cascade="all, delete-orphan")
    comments = db.relationship(
        "Comment",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="Comment.posted_at.desc()",
    )

    @property
    def booked_quantity(self):
        return sum(booking.quantity for booking in self.bookings if not booking.is_cancelled)

    @property
    def remaining_places(self):
        return max(self.capacity - self.booked_quantity, 0)

    @property
    def status(self):
        if self.cancelled:
            return "Cancelled"
        if self.event_date < date.today():
            return "Inactive"
        if self.remaining_places == 0:
            return "Sold Out"
        return "Open"

    @property
    def status_class(self):
        return self.status.lower().replace(" ", "-")

    @property
    def is_bookable(self):
        return self.status == "Open"

    @property
    def image_path(self):
        folder = "uploads" if self.image_is_upload else "img"
        return f"{folder}/{self.image_filename}"


class Booking(db.Model):
    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="uq_booking_user_event"),
    )

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(40), unique=True, nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(8, 2), nullable=False, default=Decimal("0.00"))
    booked_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)

    user = db.relationship("User", back_populates="bookings")
    event = db.relationship("Event", back_populates="bookings")

    @property
    def total_price(self):
        return Decimal(self.unit_price) * self.quantity

    @property
    def is_cancelled(self):
        return self.cancelled_at is not None

    @property
    def status(self):
        return "Cancelled" if self.is_cancelled else "Confirmed"

    @property
    def status_class(self):
        return "cancelled" if self.is_cancelled else "confirmed"

    @property
    def can_cancel(self):
        return not self.is_cancelled and self.event.status not in {"Inactive", "Cancelled"}


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(500), nullable=False)
    posted_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)

    user = db.relationship("User", back_populates="comments")
    event = db.relationship("Event", back_populates="comments")
