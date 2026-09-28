from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user
from extensions import db
from decorators import admin_required
from forms import StaffForm
from models.user import User, Role
from services.log_service import log_activity

bp = Blueprint("staff", __name__, url_prefix="/staff")
LABELS = {Role.ADMIN: "Admin", Role.MANAGER: "Manager", Role.RECEPTIONIST: "Receptionist",
          Role.HOUSEKEEPING: "Housekeeping", Role.RESTAURANT: "Restaurant staff"}


def _assignable():
    """Admins create day-to-day roles; only a Super Admin can create another Admin."""
    roles = [Role.MANAGER, Role.RECEPTIONIST, Role.HOUSEKEEPING, Role.RESTAURANT]
    return ([Role.ADMIN] + roles) if current_user.role == Role.SUPER_ADMIN else roles


@bp.route("/")
@admin_required
def list_staff():
    q = User.query.filter(User.role.in_(Role.STAFF))
    s = request.args.get("q", "").strip()
    if s:
        q = q.filter(db.or_(User.name.like(f"%{s}%"), User.email.like(f"%{s}%")))
    page = q.order_by(User.name).paginate(page=request.args.get("page", 1, type=int), per_page=10, error_out=False)
    return render_template("staff/list.html", page=page, labels=LABELS)


@bp.route("/new", methods=["GET", "POST"])
@admin_required
def create():
    form = StaffForm()
    form.role.choices = [(r, LABELS[r]) for r in _assignable()]
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            form.email.errors.append("An account with this email already exists.")
        else:
            u = User(name=form.name.data.strip(), email=email, phone=form.phone.data.strip(), role=form.role.data)
            u.set_password(form.password.data)
            db.session.add(u)
            log_activity("staff_created", f"{email} as {u.role}")
            db.session.commit()
            flash(f"{u.name} can now sign in on the staff page.", "success")
            return redirect(url_for("staff.list_staff"))
    return render_template("staff/form.html", form=form)


@bp.route("/<int:uid>/toggle", methods=["POST"])
@admin_required
def toggle(uid):
    u = db.get_or_404(User, uid)
    if u.id == current_user.id or u.role == Role.SUPER_ADMIN or (u.role == Role.ADMIN and current_user.role != Role.SUPER_ADMIN):
        abort(403)
    u.active = not u.active
    log_activity("user_status_changed", f"{u.email} -> {'active' if u.active else 'inactive'}")
    db.session.commit()
    flash(f"{u.name} is now {'active' if u.active else 'deactivated'}.", "success")
    return redirect(url_for("staff.list_staff"))
