# IMPORTS
import copy
import logging
from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from app import db, requires_roles
from models import Draw, User

# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')


# VIEWS
# View lottery page.
@lottery_blueprint.route('/lottery')
@login_required
@requires_roles('user')
def lottery():
    return render_template('lottery.html')


# Add a new draw.
@lottery_blueprint.route('/add_draw', methods=['POST'])
@login_required
@requires_roles('user')
def add_draw():
    # Create an empty submitted draws string.
    submitted_draw = ''
    # Create a boolean showing the validity of the draw.
    valid = True
    # Add input draws to the submitted draws string.
    for i in range(6):
        input_draw = request.form.get('no' + str(i + 1))
        # If one of the values is blank, flash a message and set the boolean to false.
        if input_draw == '':
            valid = False
            flash('Please do not leave any values blank.')
        else:
            if int(input_draw) > 60 or int(input_draw) < 1:
                valid = False
                flash('Draw values must be between 1 and 60.')
            else:
                submitted_draw += input_draw + ' '

    # If no values were left blank, create a new draw and add it to the database.
    if valid:
        submitted_draw.strip()

        # Create a new draw with the form data.
        new_draw = Draw(user_id=current_user.id, draw=submitted_draw, win=False, round=0,
                        draw_key=current_user.draw_key)

        # Add the new draw to the database.
        db.session.add(new_draw)
        db.session.commit()

        # Re-render lottery.page.
        flash('Draw %s submitted.' % submitted_draw)
    return lottery()


# View all draws that have not been played.
@lottery_blueprint.route('/view_draws', methods=['POST'])
@login_required
@requires_roles('user')
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
@requires_roles('user')
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
@requires_roles('user')
def play_again():
    delete_played = Draw.__table__.delete().where(Draw.played, user_id=current_user.id)
    db.session.execute(delete_played)
    db.session.commit()

    flash("All played draws deleted.")
    return lottery()
