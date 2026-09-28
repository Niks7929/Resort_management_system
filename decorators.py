from functools import wraps
from flask import abort
from flask_login import current_user, login_required
from models.user import Role


def roles_required(*roles):
    def deco(fn):
        @wraps(fn)
        @login_required
        def wrapper(*a, **kw):
            if current_user.role not in roles:
                abort(403)
            return fn(*a, **kw)
        return wrapper
    return deco


admin_required = roles_required(Role.SUPER_ADMIN, Role.ADMIN)
manager_required = roles_required(Role.SUPER_ADMIN, Role.ADMIN, Role.MANAGER)
staff_required = roles_required(*Role.STAFF)
