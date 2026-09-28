from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from extensions import db
from forms import LoginForm, RegisterForm, ChangePasswordForm
from models.user import User, Role
from services.log_service import log_activity
from routes.main import home_for

bp = Blueprint("auth", __name__)


def _safe_next(target):
    return target if target and not urlparse(target).netloc and target.startswith("/") else None


def _portal_login(portal):
    if current_user.is_authenticated:
        return redirect(home_for(current_user))
    staff_portal = portal == "staff"
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.is_locked():
            flash("Too many failed attempts. Try again in a few minutes.", "danger")
        elif user and user.check_password(form.password.data):
            if not user.active:
                flash("This account is deactivated. Contact the resort office.", "danger")
            elif user.is_staff != staff_portal:
                flash("Guests sign in on the guest page." if not user.is_staff else
                      "Staff accounts sign in on the staff page.", "warning")
            else:
                user.failed_attempts, user.locked_until = 0, None
                login_user(user)
                log_activity("login", f"{user.email} signed in ({portal})")
                db.session.commit()
                return redirect(_safe_next(request.args.get("next")) or home_for(user))
        else:
            if user:
                user.failed_attempts += 1
                if user.failed_attempts >= current_app.config["MAX_LOGIN_ATTEMPTS"]:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=current_app.config["LOCKOUT_MINUTES"])
                    user.failed_attempts = 0
                db.session.commit()
            flash("Email or password is incorrect.", "danger")
    return render_template("auth/login.html", form=form, portal=portal)


@bp.route("/login", methods=["GET", "POST"])
def login():
    return _portal_login("guest")


@bp.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    return _portal_login("staff")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(home_for(current_user))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            form.email.errors.append("An account with this email already exists.")
        else:
            u = User(name=form.name.data.strip(), email=email, phone=form.phone.data.strip(), role=Role.GUEST)
            u.set_password(form.password.data)  # role is always guest here, never user-selectable
            db.session.add(u)
            db.session.flush()
            log_activity("guest_registered", email, user=u)
            db.session.commit()
            flash("Account created. You can sign in now.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    log_activity("logout", current_user.email)
    db.session.commit()
    logout_user()
    flash("You have signed out.", "info")
    return redirect(url_for("main.index"))


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current.data):
            form.current.errors.append("Current password is incorrect.")
        else:
            current_user.set_password(form.password.data)
            log_activity("password_changed", current_user.email)
            db.session.commit()
            flash("Password updated.", "success")
            return redirect(url_for("main.dashboard"))
    return render_template("auth/change_password.html", form=form)
