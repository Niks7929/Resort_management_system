from datetime import datetime
from extensions import db

BOOKING_STATUSES = ["pending", "confirmed", "checked_in", "checked_out", "cancelled", "no_show"]
ACTIVE_STATUSES = ["pending", "confirmed", "checked_in"]
PAY_METHODS = ["Cash", "Credit Card", "Debit Card", "UPI", "Net Banking"]


class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False, index=True)
    check_in = db.Column(db.Date, nullable=False, index=True)
    check_out = db.Column(db.Date, nullable=False, index=True)
    adults = db.Column(db.Integer, default=1)
    children = db.Column(db.Integer, default=0)
    nights = db.Column(db.Integer, nullable=False)
    room_price = db.Column(db.Numeric(10, 2), nullable=False)
    service_charges = db.Column(db.Numeric(10, 2), default=0)
    discount = db.Column(db.Numeric(10, 2), default=0)
    tax = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default="confirmed", nullable=False, index=True)
    checked_in_at = db.Column(db.DateTime)
    checked_out_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guest = db.relationship("User", backref="bookings")
    room = db.relationship("Room", backref="bookings")
    payments = db.relationship("Payment", backref="booking", cascade="all, delete-orphan")

    @property
    def code(self):
        return f"BK{self.id:05d}"

    @property
    def paid(self):
        return sum((p.amount for p in self.payments if p.status != "refunded"), 0)

    @property
    def balance(self):
        return self.total - self.paid

    @property
    def payment_status(self):
        if self.paid <= 0:
            return "pending"
        return "paid" if self.balance <= 0 else "partial"


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.String(20), nullable=False)
    transaction_id = db.Column(db.String(60))
    status = db.Column(db.String(15), default="paid")
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)


class HousekeepingTask(db.Model):
    __tablename__ = "housekeeping"
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False, index=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(15), default="pending", index=True)
    notes = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    room = db.relationship("Room")
    staff = db.relationship("User")


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(60), nullable=False)
    description = db.Column(db.String(300))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user = db.relationship("User")
