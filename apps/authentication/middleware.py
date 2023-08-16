from functools import wraps
import jwt
from flask import request, redirect, request, url_for, session
from flask import current_app

from .models import Users


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('access_token')
        if not token:
            return redirect(url_for('authentication_blueprint.route_default'))
        try:
            data = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"], audience="authenticated")
            current_user = Users.query.filter_by(email=data["email"]).first()

            if not current_user:
                return {
                    "message": "Invalid Authentication token!",
                    "data": None,
                    "error": "Unauthorized"
                }, 401
        except Exception as e:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(e)
            }, 500

        return f(current_user, *args, **kwargs)

    return decorated
