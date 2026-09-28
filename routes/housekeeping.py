from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from decorators import roles_required
from models import User, Role, HousekeepingTask

bp = Blueprint("housekeeping", __name__, url_prefix="/housekeeping")
ALLOWED = (Role.SUPER_ADMIN, Role.ADMIN, Role.MANAGER, Role.HOUSEKEEPING)
STATUSES = ["pending", "assigned", "in_progress", "completed"]


@bp.route("/")
@roles_required(*ALLOWED)
def tasks():
    q = HousekeepingTask.query
    if current_user.role == Role.HOUSEKEEPING:
        q = q.filter(db.or_(HousekeepingTask.assigned_to == current_user.id, HousekeepingTask.assigned_to.is_(None)))
    staff = User.query.filter_by(role=Role.HOUSEKEEPING, active=True).all()
    return render_template("housekeeping/list.html", tasks=q.order_by(HousekeepingTask.created_at.desc()).limit(100).all(),
                           staff=staff, statuses=STATUSES)


@bp.route("/<int:tid>/update", methods=["POST"])
@roles_required(*ALLOWED)
def update(tid):
    t = db.get_or_404(HousekeepingTask, tid)
    status = request.form.get("status")
    if status in STATUSES:
        t.status = status
    staff_id = request.form.get("assigned_to", type=int)
    if staff_id and current_user.role != Role.HOUSEKEEPING:
        t.assigned_to = staff_id
        if t.status == "pending":
            t.status = "assigned"
    if t.status == "completed":
        t.completed_at = datetime.utcnow()
        t.room.status = "available"  # room is released once cleaning is completed
    db.session.commit()
    flash("Task updated.", "success")
    return redirect(url_for("housekeeping.tasks"))
