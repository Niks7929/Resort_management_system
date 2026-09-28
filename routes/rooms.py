from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from extensions import db
from decorators import manager_required
from forms import RoomForm
from models.room import Room, ROOM_TYPES, ROOM_STATUSES
from services.log_service import log_activity

bp = Blueprint("rooms", __name__, url_prefix="/rooms")


@bp.route("/")
@login_required
def list_rooms():
    q = Room.query
    s, t, st = request.args.get("q", "").strip(), request.args.get("type", ""), request.args.get("status", "")
    if s:
        q = q.filter(Room.number.like(f"%{s}%"))
    if t:
        q = q.filter_by(room_type=t)
    if st:
        q = q.filter_by(status=st)
    page = q.order_by(Room.number).paginate(page=request.args.get("page", 1, type=int), per_page=10, error_out=False)
    return render_template("rooms/list.html", page=page, types=ROOM_TYPES, statuses=ROOM_STATUSES)


def _save(room, form):
    room.number, room.room_type = form.number.data.strip(), form.room_type.data
    room.floor, room.capacity, room.price = form.floor.data, form.capacity.data, form.price.data
    room.status, room.description = form.status.data, form.description.data
    room.amenities = ",".join(form.amenities.data)


@bp.route("/new", methods=["GET", "POST"])
@manager_required
def create():
    form = RoomForm()
    if form.validate_on_submit():
        if Room.query.filter_by(number=form.number.data.strip()).first():
            form.number.errors.append("That room number already exists.")
        else:
            room = Room()
            _save(room, form)
            db.session.add(room)
            log_activity("room_created", f"Room {room.number}")
            db.session.commit()
            flash("Room added.", "success")
            return redirect(url_for("rooms.list_rooms"))
    return render_template("rooms/form.html", form=form, title="Add room")


@bp.route("/<int:rid>/edit", methods=["GET", "POST"])
@manager_required
def edit(rid):
    room = db.get_or_404(Room, rid)
    form = RoomForm(obj=room)
    if request.method == "GET":
        form.amenities.data = room.amenity_list
    if form.validate_on_submit():
        clash = Room.query.filter(Room.number == form.number.data.strip(), Room.id != rid).first()
        if clash:
            form.number.errors.append("That room number already exists.")
        else:
            _save(room, form)
            log_activity("room_updated", f"Room {room.number}")
            db.session.commit()
            flash("Room updated.", "success")
            return redirect(url_for("rooms.list_rooms"))
    return render_template("rooms/form.html", form=form, title=f"Edit room {room.number}")


@bp.route("/<int:rid>/delete", methods=["POST"])
@manager_required
def delete(rid):
    room = db.get_or_404(Room, rid)
    if room.bookings:
        flash("This room has booking history. Set it to Blocked instead of deleting.", "warning")
    else:
        log_activity("room_deleted", f"Room {room.number}")
        db.session.delete(room)
        db.session.commit()
        flash("Room deleted.", "success")
    return redirect(url_for("rooms.list_rooms"))
