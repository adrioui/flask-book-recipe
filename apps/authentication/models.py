# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin

from apps import db


class Users(db.Model, UserMixin):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    social_provider = db.Column(db.String(64))
    social_id = db.Column(db.String)
    image_url = db.Column(db.Text)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


# @login_manager.user_loader
# def user_loader(id):
#     return Users.query.filter_by(id=id).first()


# @login_manager.request_loader
# def request_loader(request):
#     username = request.form.get('username')
#     user = Users.query.filter_by(username=username).first()
#     return user if user else None
