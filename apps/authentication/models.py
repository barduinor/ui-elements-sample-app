# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import hashlib
from flask_login import UserMixin

from apps import db, login_manager

from apps.authentication.util import hash_pass

class Jwt(db.Model):
    __tablename__ = 'jwt'

    box_app_id = db.Column(db.String(128), primary_key=True)
    access_token = db.Column(db.String(2048), nullable=False)
    expires_on = db.Column(db.DateTime, nullable=False)
    app_user_id = db.Column(db.String(64),unique=True)
    box_demo_folder_id = db.Column(db.String(64),unique=False)


    def __init__(self, box_app_id, access_token, expires_on, app_user_id, box_demo_folder_id):
        self.box_app_id = box_app_id
        self.access_token = access_token
        self.expires_on = expires_on
        self.app_user_id = app_user_id
        self.box_demo_folder_id = box_demo_folder_id

    def __repr__(self):
        return str(self.box_app_id)

class User(db.Model, UserMixin):

    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(64), unique=True , nullable=False)
    password = db.Column(db.LargeBinary)
    avatar_url = db.Column(db.String(512))
    # access_token = db.Column(db.String(512))
    # refresh_token = db.Column(db.String(512))
    # box_user_id = db.Column(db.String(64),unique=True)
    # box_demo_folder_id = db.Column(db.String(64),unique=False)
    # csrf_token = db.Column(db.String(100), unique=True)

    def __init__(self, **kwargs):
        email = kwargs.get('email')
        avatar_url = kwargs.get('avatar_url')
        if avatar_url is None:
            avatar_url = 'https://www.gravatar.com/avatar/' + hashlib.md5(email.lower().encode('utf-8')).hexdigest() + '?d=identicon'
            setattr(self, 'avatar_url', avatar_url)
        
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.email)


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    return user if user else None

# @login_manager.request_loader
# def request_loader(request):
#     username = request.form.get('username')
#     user = User.query.filter_by(username=username).first()
#     return user if user else None