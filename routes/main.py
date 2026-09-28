from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models import Room, Booking, User, Payment, Role
from models.booking import ACTIVE_STATUSES
from models.landing import get_landing_settings

bp = Blueprint("main", __name__)


def home_for(user):
    return url_for("housekeeping.tasks") if user.role == Role.HOUSEKEEPING else url_for("main.dashboard")


def _d(v):
    try:
        return date.fromisoformat(v)
    except (TypeError, ValueError):
        return None


@bp.route("/")
def index():
    rooms = Room.query.filter(Room.status.notin_(["maintenance", "blocked"])).order_by(Room.price).limit(6).all()
    return render_template("landing.html", rooms=rooms, today=date.today(), settings=get_landing_settings())


@bp.route("/search")
def search():
    ci, co = _d(request.args.get("check_in")), _d(request.args.get("check_out"))
    guests = request.args.get("guests", 1, type=int)
    if not ci or not co or ci < date.today() or co <= ci:
        flash("Pick a check-in date from today onward and a check-out date after it.", "warning")
        return redirect(url_for("main.index") + "#search")
    busy = db.session.query(Booking.room_id).filter(Booking.status.in_(ACTIVE_STATUSES),
                                                    Booking.check_in < co, Booking.check_out > ci)
    rooms = (Room.query.filter(Room.status.notin_(["maintenance", "blocked"]), Room.capacity >= guests,
                               Room.id.notin_(busy)).order_by(Room.price).all())
    return render_template("search.html", rooms=rooms, ci=ci, co=co, guests=guests, nights=(co - ci).days)


@bp.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    if current_user.role == Role.HOUSEKEEPING:
        return redirect(url_for("housekeeping.tasks"))
    if not current_user.is_staff:
        mine = Booking.query.filter_by(guest_id=current_user.id).order_by(Booking.created_at.desc()).all()
        return render_template("guest_dashboard.html", bookings=mine)
    count = lambda status: Room.query.filter_by(status=status).count()
    money = lambda q: q.scalar() or 0
    paid = Payment.status != "refunded"
    stats = {
        "Total rooms": Room.query.count(), "Available": count("available"),
        "Occupied": count("occupied"), "Reserved": count("reserved"),
        "Guests": User.query.filter_by(role=Role.GUEST).count(),
        "Check-ins today": Booking.query.filter(Booking.check_in == today, Booking.status.in_(["pending", "confirmed"])).count(),
        "Check-outs today": Booking.query.filter_by(check_out=today, status="checked_in").count(),
        "Bookings": Booking.query.count(),
        "Revenue today": money(db.session.query(func.sum(Payment.amount)).filter(func.date(Payment.paid_at) == today, paid)),
        "Revenue this month": money(db.session.query(func.sum(Payment.amount)).filter(
            func.extract("month", Payment.paid_at) == today.month, func.extract("year", Payment.paid_at) == today.year, paid)),
        "Active staff": User.query.filter(User.role.in_(Role.STAFF), User.active.is_(True)).count(),
    }
    arrivals = Booking.query.filter(Booking.check_in == today, Booking.status.in_(["pending", "confirmed"])).all()
    departures = Booking.query.filter_by(check_out=today, status="checked_in").all()
    recent = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
    return render_template("dashboard.html", stats=stats, recent=recent, arrivals=arrivals, departures=departures)
