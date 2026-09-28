from datetime import datetime
from flask_login import UserMixin
from extensions import db, bcrypt, login_manager


class Role:
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"
    MANAGER = "manager"
    HOUSEKEEPING = "housekeeping"
    RESTAURANT = "restaurant"
    GUEST = "guest"
    STAFF = (SUPER_ADMIN, ADMIN, RECEPTIONIST, MANAGER, HOUSEKEEPING, RESTAURANT)
    ALL = STAFF + (GUEST,)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.GUEST, index=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    failed_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_active(self):  # Flask-Login: deactivated accounts cannot log in
        return self.active

    @property
    def is_staff(self):
        return self.role in Role.STAFF

    def set_password(self, raw):
        self.password_hash = bcrypt.generate_password_hash(raw).decode("utf-8")

    def check_password(self, raw):
        return bcrypt.check_password_hash(self.password_hash, raw)

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > datetime.utcnow())


@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))
