from functools import wraps
from flask import abort
from flask_login import current_user


def roles_required(*roles):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.active:
                abort(403)
            if current_user.role_name not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorate
