from datetime import datetime
from extensions import db

ROOM_TYPES = ["Standard", "Deluxe", "Premium", "Suite", "Family Room", "Cottage", "Villa"]
ROOM_STATUSES = ["available", "reserved", "occupied", "cleaning", "maintenance", "blocked"]
AMENITIES = ["WiFi", "AC", "TV", "Refrigerator", "Room Service", "Balcony",
             "Swimming Pool Access", "Parking", "Breakfast", "Mini Bar"]


class Room(db.Model):
    __tablename__ = "rooms"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), unique=True, nullable=False, index=True)
    room_type = db.Column(db.String(30), nullable=False, index=True)
    floor = db.Column(db.Integer, default=0)
    capacity = db.Column(db.Integer, default=2)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    amenities = db.Column(db.String(300), default="")
    image = db.Column(db.String(200))
    status = db.Column(db.String(20), default="available", nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def amenity_list(self):
        return [a for a in (self.amenities or "").split(",") if a]
