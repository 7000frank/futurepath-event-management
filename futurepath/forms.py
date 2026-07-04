from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    IntegerField,
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    InputRequired,
    Length,
    NumberRange,
    ValidationError,
)

from . import db
from .models import User


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log In")


class RegisterForm(FlaskForm):
    role = RadioField(
        "Account type",
        choices=[("student", "Student"), ("teacher", "Teacher")],
        default="student",
        validators=[DataRequired()],
    )
    first_name = StringField("First name", validators=[DataRequired(), Length(max=60)])
    last_name = StringField("Surname", validators=[DataRequired(), Length(max=60)])
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=120)])
    contact_number = StringField("Contact number", validators=[DataRequired(), Length(min=6, max=30)])
    street_address = StringField("Street address", validators=[DataRequired(), Length(min=5, max=200)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        email = field.data.strip().lower()
        if db.session.scalar(db.select(User).where(User.email == email)):
            raise ValidationError("An account already uses this email address.")


class EventForm(FlaskForm):
    title = StringField("Event title", validators=[DataRequired(), Length(min=6, max=160)])
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    presenter = StringField("Presenter or organiser", validators=[DataRequired(), Length(max=140)])
    summary = StringField("Short summary", validators=[DataRequired(), Length(min=20, max=260)])
    description = TextAreaField("Full description", validators=[DataRequired(), Length(min=50, max=3000)])
    image = FileField("Event image", validators=[FileAllowed(["jpg", "jpeg", "png"], "Use a JPG or PNG image.")])
    event_date = DateField("Event date", validators=[DataRequired()])
    start_time = TimeField("Start time", validators=[DataRequired()])
    end_time = TimeField("End time", validators=[DataRequired()])
    venue = StringField("Venue or online location", validators=[DataRequired(), Length(max=180)])
    capacity = IntegerField("Total capacity", validators=[DataRequired(), NumberRange(min=1, max=1000)])
    price = DecimalField(
        "Ticket price",
        places=2,
        default=0,
        validators=[InputRequired(), NumberRange(min=0, max=0, message="FuturePath events must be free.")],
    )
    min_score = IntegerField("Minimum demo score", validators=[InputRequired(), NumberRange(min=0, max=750)])
    max_score = IntegerField("Maximum demo score", validators=[InputRequired(), NumberRange(min=0, max=750)])
    submit = SubmitField("Save Event")

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError("End time must be after the start time.")

    def validate_max_score(self, field):
        if self.min_score.data is not None and field.data is not None and field.data < self.min_score.data:
            raise ValidationError("Maximum score must be greater than or equal to minimum score.")


class BookingForm(FlaskForm):
    submit = SubmitField("Book My Place")


class CommentForm(FlaskForm):
    body = TextAreaField("Share a question or comment", validators=[DataRequired(), Length(min=2, max=500)])
    submit = SubmitField("Post Comment")


class EmptyForm(FlaskForm):
    submit = SubmitField("Confirm")
