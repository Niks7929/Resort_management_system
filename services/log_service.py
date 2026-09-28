from flask import request
from flask_login import current_user
from extensions import db
from models.booking import ActivityLog


def log_activity(action, description="", user=None):
    u = user or (current_user if current_user.is_authenticated else None)
    db.session.add(ActivityLog(user_id=u.id if u else None, action=action, description=description[:300],
                               ip_address=request.remote_addr))
