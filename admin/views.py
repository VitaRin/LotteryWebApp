# IMPORTS
import copy

from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from app import db, requires_roles
from models import User, Draw

# CONFIG
admin_blueprint = Blueprint('admin', __name__, template_folder='templates')


# VIEWS
# View admin homepage.
@admin_blueprint.route('/admin')
@login_required
@requires_roles('admin')
def admin():
    return render_template('admin.html', name=current_user.firstname)


# View all registered users.
@admin_blueprint.route('/view_all_users', methods=['POST'])
@login_required
@requires_roles('admin')
def view_all_users():
    return render_template('admin.html', name=current_user.firstname,
                           current_users=User.query.filter_by(role='user').all())


# Create a new winning draw.
@admin_blueprint.route('/create_winning_draw', methods=['POST'])
@login_required
@requires_roles('admin')
def create_winning_draw():

    # Get current winning draw.
    current_winning_draw = Draw.query.filter_by(win=True).first()
    round = 1

    # If a current winning draw exists.
    if current_winning_draw:
        # Update lottery round by 1.
        round = current_winning_draw.round + 1

        # Delete current winning draw.
        db.session.delete(current_winning_draw)
        db.session.commit()

    # Get new winning draw entered in form.
    submitted_draw = ''
    for i in range(6):
        submitted_draw += request.form.get('no' + str(i + 1)) + ' '
    # Remove any surrounding whitespace.
    submitted_draw.strip()

    # Create a new draw object with the form data.
    new_winning_draw = Draw(user_id=current_user.id, draw=submitted_draw, win=True, round=round, draw_key=current_user.draw_key)

    # Add the new winning draw to the database.
    db.session.add(new_winning_draw)
    db.session.commit()

    # Re-render admin page.
    flash("New winning draw added.")
    return admin()


# View current winning draw.
@admin_blueprint.route('/view_winning_draw', methods=['POST'])
@login_required
@requires_roles('admin')
def view_winning_draw():

    # Get winning draw from DB.
    current_winning_draw = Draw.query.filter_by(win=True).first()

    # If a winning draw exists.
    if current_winning_draw:
        # Create a copy of the winning draw independent of the database.
        winning_draw_copy = copy.deepcopy(current_winning_draw)
        # Decrypt the winning draw copy.
        winning_draw_copy.view_draw(current_user.draw_key)
        # Re-render admin page with current winning draw and lottery round.
        return render_template('admin.html', winning_draw=winning_draw_copy, name=current_user.firstname)

    # If no winning draw exists, rerender admin page.
    flash("No winning draw exists. Please add a winning draw.")
    return admin()


# View lottery results and winners.
@admin_blueprint.route('/run_lottery', methods=['POST'])
@login_required
@requires_roles('admin')
def run_lottery():

    # Get current unplayed winning draw.
    current_winning_draw = Draw.query.filter_by(win=True, played=False).first()

    # If current unplayed winning draw exists.
    if current_winning_draw:

        # Get all unplayed user draws.
        user_draws = Draw.query.filter_by(win=False, played=False).all()
        results = []

        # If at least one unplayed user draw exists.
        if user_draws:

            # Update current winning draw as played.
            current_winning_draw.played = True
            db.session.add(current_winning_draw)
            db.session.commit()

            # For each unplayed user draw.
            for draw in user_draws:

                # Get the owning user (instance/object)
                user = User.query.filter_by(id=draw.user_id).first()

                # If user draw matches current unplayed winning draw.
                if draw.draw == current_winning_draw.draw:

                    # Add details of winner to list of results.
                    results.append((current_winning_draw.round, draw.draw, draw.user_id, user.email))

                    # Update draw as a winning draw (this will be used to highlight winning draws in the user's
                    # lottery page).
                    draw.match = True

                # Update draw as played.
                draw.played = True

                # Update draw with current lottery round.
                draw.round = current_winning_draw.round

                # Commit draw changes to DB.
                db.session.add(draw)
                db.session.commit()

            # If no winners.
            if len(results) == 0:
                flash("No winners.")

            return render_template('admin.html', results=results, name=current_user.firstname)

        flash("No user draws entered.")
        return admin()

    # If current unplayed winning draw does not exist.
    flash("Current winning draw expired. Add new winning draw for next round.")
    return admin()


# View last 10 log entries.
@admin_blueprint.route('/logs', methods=['POST'])
@login_required
@requires_roles('admin')
def logs():
    with open("lottery.log", "r") as f:
        content = f.read().splitlines()[-10:]
        content.reverse()

    return render_template('admin.html', logs=content, name=current_user.firstname)
