# IMPORTS
import logging
from functools import wraps

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import current_user

from app import db
from models import User
from users.forms import RegisterForm, LoginForm

# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')


# VIEWS
# View registration.
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # Create signup form object.
    form = RegisterForm()

    # If request method is POST or form is valid.
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # If this returns a user, then the email already exists in database.

        # If email already exists redirect user back to signup page with error message so user can try again.
        if user:
            flash('Email address already exists')
            return render_template('register.html', form=form)

        # Create a new user with the form data.
        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        phone=form.phone.data,
                        password=form.password.data,
                        pin_key=form.pin_key.data,
                        role='user')

        # Add the new user to the database.
        db.session.add(new_user)
        db.session.commit()

        # Sends user to login page.
        return redirect(url_for('users.login'))
    # If request method is GET or form not valid re-render signup page.
    return render_template('register.html', form=form)


# View user login.
@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        return render_template('profile.html')

    return render_template('login.html', form=form)


# View user profile.
@users_blueprint.route('/profile')
def profile():
    return render_template('profile.html', name="PLACEHOLDER FOR FIRSTNAME")


# View user account.
@users_blueprint.route('/account')
def account():
    return render_template('account.html',
                           acc_no="PLACEHOLDER FOR USER ID",
                           email="PLACEHOLDER FOR USER EMAIL",
                           firstname="PLACEHOLDER FOR USER FIRSTNAME",
                           lastname="PLACEHOLDER FOR USER LASTNAME",
                           phone="PLACEHOLDER FOR USER PHONE")
