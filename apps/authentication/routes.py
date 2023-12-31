# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import flask
from flask import render_template, redirect, request, url_for, session

from apps import db
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users
from apps.config import Config


@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login & Registration
@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)

    if flask.request.method == 'POST':

        # read form data
        email = request.form['email']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(email=email).first()

        # Check the password
        if user:
            try:
                is_validated = Config.supabase.auth.sign_in_with_password(
                    {"email": email, "password": password})

                session["access_token"] = is_validated.session.access_token

                return redirect(url_for('authentication_blueprint.route_default'))

            except Exception as e:
                # Handle the authentication error here
                return render_template('accounts/login.html',
                                       msg='Wrong email or password: ' +
                                           str(e),
                                       form=login_form)

    if not session.get("access_token"):
        return render_template('accounts/login.html',
                               form=login_form)
    else:
        return redirect(url_for('recipe_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()

        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        response = Config.supabase.auth.sign_up(
            {'email': email, 'password': password})

        if response:
            # else we can create the user
            user = Users(
                email=email,
                username=username
            )
            db.session.add(user)
            db.session.commit()

        # Delete user from session
        session.clear()

        return render_template('accounts/register.html',
                               msg='User created successfully.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    response = Config.supabase.auth.sign_out()
    if response is not None:
        return {'message': 'Logout failed!'}
    session.clear()
    return redirect(url_for('authentication_blueprint.login'))
