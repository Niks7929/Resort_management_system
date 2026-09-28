from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from decorators import staff_required, roles_required
from forms import BookingForm, PaymentForm
from models import Booking, Room, User, Payment, Role
from models.booking import BOOKING_STATUSES
from services import booking_service as bs
from services.log_service import log_activity

bp = Blueprint("bookings", __name__, url_prefix="/bookings")
FRONT_DESK = (Role.SUPER_ADMIN, Role.ADMIN, Role.MANAGER, Role.RECEPTIONIST)


def _own_or_staff(booking):
    if current_user.is_staff and current_user.role not in FRONT_DESK:
        abort(403)
    if not current_user.is_staff and booking.guest_id != current_user.id:
        abort(404)


def _fill_choices(form):
    form.room_id.choices = [(r.id, f"{r.number} · {r.room_type} · {r.price}") for r in
                            Room.query.filter(~Room.status.in_(["maintenance", "blocked"])).order_by(Room.number)]
    form.guest_id.choices = [(u.id, f"{u.name} ({u.email})") for u in
                             User.query.filter_by(role=Role.GUEST, active=True).order_by(User.name)]


@bp.route("/")
@login_required
def list_bookings():
    if current_user.is_staff and current_user.role not in FRONT_DESK:
        abort(403)
    q = Booking.query
    if not current_user.is_staff:
        q = q.filter_by(guest_id=current_user.id)
    s, st = request.args.get("q", "").strip(), request.args.get("status", "")
    if s:
        q = q.join(User, Booking.guest_id == User.id).join(Room, Booking.room_id == Room.id).filter(
            db.or_(User.name.like(f"%{s}%"), User.phone.like(f"%{s}%"), Room.number.like(f"%{s}%"),
                   Booking.id == (int(s[2:]) if s.upper().startswith("BK") and s[2:].isdigit() else -1)))
    if st:
        q = q.filter(Booking.status == st)
    page = q.order_by(Booking.created_at.desc()).paginate(page=request.args.get("page", 1, type=int), per_page=10, error_out=False)
    return render_template("bookings/list.html", page=page, statuses=BOOKING_STATUSES)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if current_user.is_staff and current_user.role not in FRONT_DESK:
        abort(403)
    form = BookingForm()
    _fill_choices(form)
    if request.method == "GET":
        from routes.main import _d
        form.room_id.data = request.args.get("room", type=int)
        form.check_in.data, form.check_out.data = _d(request.args.get("check_in")), _d(request.args.get("check_out"))
        form.adults.data = request.args.get("guests", 1, type=int)
    if form.validate_on_submit():
        guest_id = form.guest_id.data if current_user.role in FRONT_DESK else current_user.id
        room = db.get_or_404(Room, form.room_id.data)
        if form.check_in.data < date.today():
            form.check_in.errors.append("Check-in cannot be in the past.")
        else:
            try:
                b = bs.save_booking(Booking(status="confirmed"), room, guest_id, form.check_in.data, form.check_out.data,
                                    form.adults.data, form.children.data,
                                    form.discount.data if current_user.role in FRONT_DESK else 0)
                db.session.flush()
                log_activity("booking_created", f"{b.code} room {room.number}")
                db.session.commit()
                flash(f"Booking {b.code} confirmed.", "success")
                return redirect(url_for("bookings.view", bid=b.id))
            except bs.BookingError as e:
                flash(str(e), "danger")
    return render_template("bookings/form.html", form=form, front_desk=current_user.role in FRONT_DESK)


@bp.route("/<int:bid>")
@login_required
def view(bid):
    b = db.get_or_404(Booking, bid)
    _own_or_staff(b)
    return render_template("bookings/view.html", b=b, pay_form=PaymentForm())


def _transition(bid, fn, done, action, roles=None):
    b = db.get_or_404(Booking, bid)
    _own_or_staff(b)
    try:
        fn(b)
        log_activity(action, b.code)
        db.session.commit()
        flash(done, "success")
    except bs.BookingError as e:
        flash(str(e), "danger")
    return redirect(url_for("bookings.view", bid=bid))


@bp.route("/<int:bid>/cancel", methods=["POST"])
@login_required
def cancel(bid):
    return _transition(bid, bs.cancel, "Booking cancelled.", "booking_cancelled")


@bp.route("/<int:bid>/check-in", methods=["POST"])
@roles_required(*FRONT_DESK)
def check_in(bid):
    return _transition(bid, bs.check_in, "Guest checked in.", "check_in")


@bp.route("/<int:bid>/check-out", methods=["POST"])
@roles_required(*FRONT_DESK)
def check_out(bid):
    return _transition(bid, bs.check_out, "Guest checked out. Housekeeping task created.", "check_out")


@bp.route("/<int:bid>/pay", methods=["POST"])
@roles_required(*FRONT_DESK)
def pay(bid):
    b = db.get_or_404(Booking, bid)
    form = PaymentForm()
    if form.validate_on_submit():
        if form.amount.data > b.balance:
            flash("Payment is more than the balance due.", "danger")
        else:
            db.session.add(Payment(booking_id=b.id, amount=form.amount.data, method=form.method.data,
                                   transaction_id=form.transaction_id.data or None))
            log_activity("payment_added", f"{b.code} {form.amount.data}")
            db.session.commit()
            flash("Payment recorded.", "success")
    else:
        flash("Enter a valid payment amount.", "danger")
    return redirect(url_for("bookings.view", bid=bid))
