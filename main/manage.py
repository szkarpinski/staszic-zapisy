import configparser
from main.db import get_db
from flask import (
    Blueprint, render_template, flash
)
from main.db import get_db

bp = Blueprint('manage', __name__)

@bp.route('/manage/<string:key>', methods=('GET', 'POST'))
def panel(key):
    db = get_db()
    email = 'hugo@staszic.waw.pl'

    terminy = db.execute(
        'SELECT * FROM wizyty JOIN nauczyciele ON wizyty.id_nauczyciela=nauczyciele.id WHERE email_rodzica = ? ORDER BY godzina', (email,)
    ).fetchall()
    return render_template('zapisy/manage.html', email=email, terminy=terminy)

