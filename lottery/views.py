# IMPORTS
import copy
import logging
from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from app import db
from models import Draw, User

# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')


# VIEWS
# View lottery page.
@lottery_blueprint.route('/lottery')
@login_required
def lottery():
    return render_template('lottery.html')


@lottery_blueprint.route('/add_draw', methods=['POST'])
@login_required
def add_draw():
    submitted_draw = ''
    for i in range(6):
        submitted_draw += request.form.get('no' + str(i + 1)) + ' '
    submitted_draw.strip()

    # Create a new draw with the form data.
    new_draw = Draw(user_id=current_user.id, draw=submitted_draw, win=False, round=0, draw_key=current_user.draw_key)

    # Add the new draw to the database.
    db.session.add(new_draw)
    db.session.commit()

    # Re-render lottery.page.
    flash('Draw %s submitted.' % submitted_draw)
    return lottery()


# View all draws that have not been played.
@lottery_blueprint.route('/view_draws', methods=['POST'])
@login_required
def view_draws():
    # Get all draws that have not been played [played=0].
    playable_draws = Draw.query.filter_by(played=False, user_id=current_user.id).all()

    # If playable draws exist.
    if len(playable_draws) != 0:

        # Create a list of copied draws which are independent of the database.
        draw_copies = list(map(lambda x: copy.deepcopy(x), playable_draws))

        # Empty list for decrypted copied draws.
        decrypted_draws = []

        # Decrypt each draw and add it to decrypted_draws array.
        for d in draw_copies:
            d.view_draw(current_user.draw_key)
            decrypted_draws.append(d)

        # Re-render lottery page with playable draws.
        return render_template('lottery.html', playable_draws=decrypted_draws)
    else:
        flash('No playable draws.')
        return lottery()


# View lottery results.
@lottery_blueprint.route('/check_draws', methods=['POST'])
@login_required
def check_draws():
    # Get played draws.
    played_draws = Draw.query.filter_by(played=True, user_id=current_user.id).all()

    # If played draws exist.
    if len(played_draws) != 0:
        # Create a list of copied draws which are independent of the database.
        draw_copies = list(map(lambda x: copy.deepcopy(x), played_draws))

        # Empty list for decrypted copied draws.
        decrypted_draws = []

        # Decrypt each draw and add it to decrypted_draws array.
        for d in draw_copies:
            d.view_draw(current_user.draw_key)
            decrypted_draws.append(d)

        return render_template('lottery.html', results=draw_copies, played=True)

    # If no played draws exist [all draw entries have been played therefore wait for next lottery round].
    else:
        flash("Next round of lottery yet to play. Check you have playable draws.")
        return lottery()


# Delete all played draws.
@lottery_blueprint.route('/play_again', methods=['POST'])
@login_required
def play_again():
    delete_played = Draw.__table__.delete().where(Draw.played, user_id=current_user.id)
    db.session.execute(delete_played)
    db.session.commit()

    flash("All played draws deleted.")
    return lottery()
