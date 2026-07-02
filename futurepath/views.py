from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from . import db
from .forms import BookingForm, CommentForm, EmptyForm, EventForm
from .models import Booking, Category, Comment, Event


main_bp = Blueprint("main", __name__)


def category_choices():
    categories = db.session.scalars(db.select(Category).order_by(Category.name)).all()
    return [(category.id, category.name) for category in categories]


def save_image(file_storage):
    original = secure_filename(file_storage.filename)
    suffix = Path(original).suffix.lower() or ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    file_storage.save(Path(current_app.config["UPLOAD_FOLDER"]) / filename)
    return filename


def require_owner(event):
    require_teacher()
    if event.owner_id != current_user.id:
        abort(403)


def require_teacher():
    if not current_user.is_teacher:
        abort(403)


def current_user_bookings_by_event():
    if not current_user.is_authenticated:
        return {}
    statement = db.select(Booking).where(
        Booking.user_id == current_user.id,
        Booking.cancelled_at.is_(None),
    )
    return {booking.event_id: booking for booking in db.session.scalars(statement)}


@main_bp.route("/")
def index():
    search_text = request.args.get("q", "").strip()
    category_slug = request.args.get("category", "").strip()
    status_filter = request.args.get("status", "").strip()

    statement = db.select(Event).join(Category)
    if search_text:
        term = f"%{search_text}%"
        statement = statement.where(
            or_(
                Event.title.ilike(term),
                Event.summary.ilike(term),
                Event.description.ilike(term),
                Event.venue.ilike(term),
                Event.presenter.ilike(term),
            )
        )
    if category_slug:
        statement = statement.where(Category.slug == category_slug)
    events = db.session.scalars(statement.order_by(Event.event_date, Event.start_time)).all()
    if status_filter:
        events = [event for event in events if event.status_class == status_filter]
    events.sort(
        key=lambda event: (
            0 if event.status in {"Open", "Sold Out"} else 1 if event.status == "Cancelled" else 2,
            event.event_date,
            event.start_time,
        )
    )

    categories = db.session.scalars(db.select(Category).order_by(Category.name)).all()
    return render_template(
        "index.html",
        events=events,
        categories=categories,
        search_text=search_text,
        category_slug=category_slug,
        status_filter=status_filter,
        user_bookings_by_event=current_user_bookings_by_event(),
    )


@main_bp.route("/score-finder")
def score_finder():
    raw_score = request.args.get("score", "").strip()
    score = None
    events = []
    if raw_score:
        try:
            score = int(raw_score)
        except ValueError:
            score = None
        if score is None or not 0 <= score <= 750:
            flash("Enter a Gaokao score from 0 to 750.", "danger")
            score = None
        else:
            statement = (
                db.select(Event)
                .where(Event.min_score <= score, Event.max_score >= score)
                .order_by(Event.event_date, Event.start_time)
            )
            events = [
                event
                for event in db.session.scalars(statement).all()
                if event.status in {"Open", "Sold Out"}
            ]
    return render_template(
        "recommendations.html",
        score=score,
        raw_score=raw_score,
        events=events,
        user_bookings_by_event=current_user_bookings_by_event(),
    )


@main_bp.route("/events/<int:event_id>")
def event_detail(event_id):
    event = db.get_or_404(Event, event_id)
    existing_booking = None
    if current_user.is_authenticated:
        existing_booking = db.session.scalar(
            db.select(Booking).where(
                Booking.user_id == current_user.id,
                Booking.event_id == event.id,
            )
        )
    return render_template(
        "event_detail.html",
        event=event,
        booking_form=BookingForm(),
        comment_form=CommentForm(),
        cancel_form=EmptyForm(),
        existing_booking=existing_booking,
    )


@main_bp.route("/events/create", methods=["GET", "POST"])
@login_required
def create_event():
    require_teacher()
    form = EventForm()
    form.category_id.choices = category_choices()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data.strip(),
            summary=form.summary.data.strip(),
            description=form.description.data.strip(),
            event_date=form.event_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            venue=form.venue.data.strip(),
            presenter=form.presenter.data.strip(),
            capacity=form.capacity.data,
            price=Decimal("0.00"),
            min_score=form.min_score.data,
            max_score=form.max_score.data,
            owner=current_user,
            category_id=form.category_id.data,
        )
        if form.image.data:
            event.image_filename = save_image(form.image.data)
            event.image_is_upload = True
        db.session.add(event)
        db.session.commit()
        flash("Your free event has been published with an Open status.", "success")
        return redirect(url_for("main.event_detail", event_id=event.id))
    return render_template("event_form.html", form=form, event=None, heading="Create a Nonprofit Event")


@main_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    event = db.get_or_404(Event, event_id)
    require_owner(event)
    form = EventForm(obj=event)
    form.category_id.choices = category_choices()
    if request.method == "GET":
        form.category_id.data = event.category_id
    if form.validate_on_submit():
        if form.capacity.data < event.booked_quantity:
            flash(
                f"Capacity cannot be lower than the {event.booked_quantity} place(s) already booked.",
                "danger",
            )
            return render_template("event_form.html", form=form, event=event, heading="Update Event")
        event.title = form.title.data.strip()
        event.summary = form.summary.data.strip()
        event.description = form.description.data.strip()
        event.event_date = form.event_date.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.venue = form.venue.data.strip()
        event.presenter = form.presenter.data.strip()
        event.capacity = form.capacity.data
        event.price = Decimal("0.00")
        event.min_score = form.min_score.data
        event.max_score = form.max_score.data
        event.category_id = form.category_id.data
        if form.image.data:
            event.image_filename = save_image(form.image.data)
            event.image_is_upload = True
        db.session.commit()
        flash("Event details have been updated.", "success")
        return redirect(url_for("main.event_detail", event_id=event.id))
    return render_template("event_form.html", form=form, event=event, heading="Update Event")


@main_bp.route("/events/<int:event_id>/cancel", methods=["POST"])
@login_required
def cancel_event(event_id):
    event = db.get_or_404(Event, event_id)
    require_owner(event)
    form = EmptyForm()
    if form.validate_on_submit():
        event.cancelled = True
        db.session.commit()
        flash("The event has been cancelled.", "info")
    else:
        flash("The cancellation request could not be validated.", "danger")
    return redirect(url_for("main.event_detail", event_id=event.id))


@main_bp.route("/events/<int:event_id>/book", methods=["POST"])
@login_required
def book_event(event_id):
    event = db.get_or_404(Event, event_id)
    form = BookingForm()
    if not form.validate_on_submit():
        flash("The booking request could not be validated.", "danger")
        return redirect(url_for("main.event_detail", event_id=event.id))
    existing_booking = db.session.scalar(
        db.select(Booking).where(
            Booking.user_id == current_user.id,
            Booking.event_id == event.id,
        )
    )
    if existing_booking and not existing_booking.is_cancelled:
        flash("You have already booked this event.", "info")
        return redirect(url_for("main.event_detail", event_id=event.id))
    if not event.is_bookable:
        flash(f"This event is {event.status.lower()} and cannot accept bookings.", "danger")
        return redirect(url_for("main.event_detail", event_id=event.id))
    if event.remaining_places < 1:
        flash("No places remain. The booking was not created.", "danger")
        return redirect(url_for("main.event_detail", event_id=event.id))

    reference = f"FP{datetime.now():%Y%m%d}{uuid4().hex[:8].upper()}"
    if existing_booking:
        existing_booking.reference = reference
        existing_booking.quantity = 1
        existing_booking.unit_price = event.price
        existing_booking.booked_at = datetime.now()
        existing_booking.cancelled_at = None
    else:
        booking = Booking(
            reference=reference,
            quantity=1,
            unit_price=event.price,
            user=current_user,
            event=event,
        )
        db.session.add(booking)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("You already have an active booking for this event.", "info")
        return redirect(url_for("main.event_detail", event_id=event.id))
    flash(f"Booking confirmed. Your reference is {reference}.", "success")
    return redirect(url_for("main.event_detail", event_id=event.id))


@main_bp.route("/events/<int:event_id>/comments", methods=["POST"])
@login_required
def post_comment(event_id):
    event = db.get_or_404(Event, event_id)
    form = CommentForm()
    if form.validate_on_submit():
        db.session.add(Comment(body=form.body.data.strip(), user=current_user, event=event))
        db.session.commit()
        flash("Your comment has been posted.", "success")
    else:
        flash("Enter a comment between 2 and 500 characters.", "danger")
    return redirect(url_for("main.event_detail", event_id=event.id) + "#comments")


@main_bp.route("/bookings")
@login_required
def bookings():
    statement = db.select(Booking).where(Booking.user_id == current_user.id).order_by(Booking.booked_at.desc())
    user_bookings = db.session.scalars(statement).all()
    return render_template("bookings.html", bookings=user_bookings, cancel_form=EmptyForm())


@main_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    if booking.user_id != current_user.id:
        abort(403)

    form = EmptyForm()
    if not form.validate_on_submit():
        flash("The cancellation request could not be validated.", "danger")
    elif booking.is_cancelled:
        flash("This booking has already been cancelled.", "info")
    elif not booking.can_cancel:
        flash("Past or cancelled events cannot be cancelled from booking history.", "danger")
    else:
        booking.cancelled_at = datetime.now()
        db.session.commit()
        flash(
            f"Booking {booking.reference} has been cancelled and {booking.quantity} place(s) released.",
            "success",
        )
    return redirect(url_for("main.bookings"))
