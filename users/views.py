# IMPORTS
import logging
from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import db, requires_roles
from models import User
from users.forms import RegisterForm, LoginForm
import pyotp

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

        # Update logs that a new user has registered.
        logging.warning('SECURITY - User registration [%s, %s]', form.email.data, request.remote_addr)

        # Sends user to login page.
        return redirect(url_for('users.login'))
    # If request method is GET or form not valid re-render signup page.
    return render_template('register.html', form=form)


# View user login.
@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():

    # If session attribute logins does not exist create a new one.
    if not session.get('logins'):
        session['logins'] = 0
    # If login attempts is 3 or more create an error message.
    elif session.get('logins') >= 3:
        flash('Number of incorrect logins exceeded.')

    form = LoginForm()

    if form.validate_on_submit():

        # Increase login attempts by 1.
        session['logins'] += 1

        # Check whether the entered email is in the database.
        user = User.query.filter_by(email=form.username.data).first()

        # Check if the entered password matches the password stored in the database.
        if not user or not check_password_hash(user.password, form.password.data):

            # Update logs that an invalid login attempt was made.
            logging.warning('SECURITY - Invalid login attempt [%s, %s]', form.username.data, request.remote_addr)

            # If no match create an appropriate error message based on login attempts.
            if session['logins'] == 3:
                flash('Number of incorrect logins exceeded.')
            elif session['logins'] == 2:
                flash('Please check your login details and try again. 1 login attempt remaining.')
            else:
                flash('Please check your login details and try again. 2 login attempts remaining.')

            return render_template('login.html', form=form)

        if pyotp.TOTP(user.pin_key).verify(form.pin.data):
            # If user is verified reset login attempts to 0.
            session['logins'] = 0

            login_user(user)

            # Update the user's last and current login times.
            user.last_logged_in = user.current_logged_in
            user.current_logged_in = datetime.now()
            db.session.commit()

            # Update logs that a user has logged in.
            logging.warning('SECURITY - Log in [%s, %s, %s]', current_user.id, current_user.email, request.remote_addr)

            # Redirect users to role appropriate pages.
            if current_user.role == 'admin':
                return redirect(url_for('admin.admin'))
            else:
                return redirect(url_for('users.profile'))

        else:
            flash("You have supplied an invalid 2FA token!", "danger")

    return render_template('login.html', form=form)


# Logout user.
@users_blueprint.route('/logout')
@login_required
def logout():
    # Update logs that a user has logged out.
    logging.warning('SECURITY - Log out [%s, %s, %s]', current_user.id, current_user.email, request.remote_addr)

    logout_user()
    return redirect(url_for('index'))


# View user profile.
@users_blueprint.route('/profile')
@login_required
@requires_roles('user')
def profile():
    return render_template('profile.html', name=current_user.firstname)


# View user account.
@users_blueprint.route('/account')
@login_required
def account():
    return render_template('account.html',
                           acc_no=current_user.id,
                           email=current_user.email,
                           firstname=current_user.firstname,
                           lastname=current_user.lastname,
                           phone=current_user.phone)
