from datetime import datetime
from decimal import Decimal
from flask import current_app
from extensions import db
from models.booking import Booking, HousekeepingTask, ACTIVE_STATUSES
from models.room import Room


class BookingError(Exception):
    pass


def has_overlap(room_id, check_in, check_out, exclude_id=None):
    """Two stays overlap when each starts before the other ends (check-out day is free)."""
    q = Booking.query.filter(Booking.room_id == room_id, Booking.status.in_(ACTIVE_STATUSES),
                             Booking.check_in < check_out, Booking.check_out > check_in)
    if exclude_id:
        q = q.filter(Booking.id != exclude_id)
    return db.session.query(q.exists()).scalar()


def calculate(room, check_in, check_out, discount=0, services=0):
    nights = (check_out - check_in).days
    if nights < 1:
        raise BookingError("Check-out must be after check-in.")
    price = Decimal(room.price)
    room_total = price * nights
    discount = min(Decimal(discount or 0), room_total)
    taxable = room_total + Decimal(services) - discount
    tax = (taxable * Decimal(str(current_app.config["TAX_RATE"]))).quantize(Decimal("0.01"))
    return dict(nights=nights, room_price=price, discount=discount, tax=tax, total=taxable + tax)


def save_booking(booking, room, guest_id, check_in, check_out, adults, children, discount):
    if room.status in ("maintenance", "blocked"):
        raise BookingError("This room is not open for booking.")
    if adults + children > room.capacity:
        raise BookingError(f"Room {room.number} sleeps {room.capacity} guests at most.")
    if has_overlap(room.id, check_in, check_out, booking.id):
        raise BookingError("This room is already booked for some of those dates.")
    calc = calculate(room, check_in, check_out, discount, booking.service_charges or 0)
    booking.guest_id, booking.room_id = guest_id, room.id
    booking.check_in, booking.check_out = check_in, check_out
    booking.adults, booking.children = adults, children
    for k, v in calc.items():
        setattr(booking, k, v)
    db.session.add(booking)
    return booking


def check_in(booking):
    if booking.status not in ("pending", "confirmed"):
        raise BookingError("Only pending or confirmed bookings can check in.")
    booking.status, booking.checked_in_at = "checked_in", datetime.utcnow()
    booking.room.status = "occupied"


def check_out(booking):
    if booking.status != "checked_in":
        raise BookingError("Only checked-in bookings can check out.")
    if booking.balance > 0:
        raise BookingError(f"Collect the outstanding balance of {booking.balance} before check-out.")
    booking.status, booking.checked_out_at = "checked_out", datetime.utcnow()
    booking.room.status = "cleaning"
    db.session.add(HousekeepingTask(room_id=booking.room_id, notes=f"Post-checkout clean ({booking.code})"))


def cancel(booking):
    if booking.status not in ("pending", "confirmed"):
        raise BookingError("This booking can no longer be cancelled.")
    booking.status = "cancelled"
