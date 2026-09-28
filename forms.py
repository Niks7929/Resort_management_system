import re
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, IntegerField, DecimalField,
                     DateField, TextAreaField, SelectMultipleField, SubmitField)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, URL, ValidationError
from models.room import ROOM_TYPES, ROOM_STATUSES, AMENITIES
from models.booking import PAY_METHODS


def strong_password(form, field):
    p = field.data or ""
    ok = (len(p) >= 8 and re.search(r"[A-Z]", p) and re.search(r"[a-z]", p)
          and re.search(r"\d", p) and re.search(r"[^A-Za-z0-9]", p))
    if not ok:
        raise ValidationError("Use 8+ characters with an uppercase letter, a lowercase letter, a number and a symbol.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    phone = StringField("Phone", validators=[DataRequired(), Length(min=7, max=20)])
    password = PasswordField("Password", validators=[DataRequired(), strong_password])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password", "Passwords must match.")])


class ChangePasswordForm(FlaskForm):
    current = PasswordField("Current password", validators=[DataRequired()])
    password = PasswordField("New password", validators=[DataRequired(), strong_password])
    confirm = PasswordField("Confirm new password", validators=[DataRequired(), EqualTo("password", "Passwords must match.")])


class RoomForm(FlaskForm):
    number = StringField("Room number", validators=[DataRequired(), Length(max=10)])
    room_type = SelectField("Type", choices=[(t, t) for t in ROOM_TYPES])
    floor = IntegerField("Floor", default=0, validators=[NumberRange(min=0, max=100)])
    capacity = IntegerField("Capacity", default=2, validators=[NumberRange(min=1, max=20)])
    price = DecimalField("Price per night", validators=[DataRequired(), NumberRange(min=1)])
    status = SelectField("Status", choices=[(s, s.title()) for s in ROOM_STATUSES])
    amenities = SelectMultipleField("Amenities", choices=[(a, a) for a in AMENITIES])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])


class BookingForm(FlaskForm):
    guest_id = SelectField("Guest", coerce=int, validators=[Optional()])
    room_id = SelectField("Room", coerce=int, validators=[DataRequired()])
    check_in = DateField("Check-in", validators=[DataRequired()])
    check_out = DateField("Check-out", validators=[DataRequired()])
    adults = IntegerField("Adults", default=1, validators=[NumberRange(min=1, max=20)])
    children = IntegerField("Children", default=0, validators=[NumberRange(min=0, max=20)])
    discount = DecimalField("Discount", default=0, validators=[Optional(), NumberRange(min=0)])


class PaymentForm(FlaskForm):
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=1)])
    method = SelectField("Method", choices=[(m, m) for m in PAY_METHODS])
    transaction_id = StringField("Transaction ID", validators=[Optional(), Length(max=60)])


class StaffForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Work email", validators=[DataRequired(), Email(), Length(max=150)])
    phone = StringField("Phone", validators=[DataRequired(), Length(min=7, max=20)])
    role = SelectField("Role", validators=[DataRequired()])
    password = PasswordField("Temporary password", validators=[DataRequired(), strong_password])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password", "Passwords must match.")])


class LandingSettingsForm(FlaskForm):
    resort_name = StringField("Resort name", validators=[DataRequired(), Length(max=120)])
    resort_address = StringField("Address", validators=[DataRequired(), Length(max=255)])
    hero_kicker = StringField("Small heading", validators=[DataRequired(), Length(max=120)])
    hero_title = StringField("Main heading", validators=[DataRequired(), Length(max=180)])
    hero_description = TextAreaField("Supporting text", validators=[DataRequired(), Length(max=300)])
    hero_image_url = StringField("Hero photo URL", validators=[DataRequired(), Length(max=500), URL()])
    intro_title = StringField("About heading", validators=[DataRequired(), Length(max=120)])
    intro_description = TextAreaField("About text", validators=[DataRequired(), Length(max=2000)])
    intro_image_url = StringField("About photo URL", validators=[DataRequired(), Length(max=500), URL()])
    dining_title = StringField("Dining heading", validators=[DataRequired(), Length(max=120)])
    dining_description = TextAreaField("Dining text", validators=[DataRequired(), Length(max=2000)])
    dining_image_url = StringField("Dining photo URL", validators=[DataRequired(), Length(max=500), URL()])
    contact_title = StringField("Contact heading", validators=[DataRequired(), Length(max=120)])
    contact_description = TextAreaField("Contact text", validators=[DataRequired(), Length(max=300)])
    phone = StringField("Phone", validators=[DataRequired(), Length(max=40)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
