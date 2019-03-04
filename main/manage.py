import configparser
import functools
from itsdangerous import Serializer, BadSignature
from main.db import get_db
from flask import (
    Blueprint, render_template, flash, redirect, url_for, session, g, current_app
)
from main.db import get_db


bp = Blueprint('manage', __name__, url_prefix='/manage')


@bp.before_app_request
def load_parent():
    db = get_db()
    id = session['rodzic']

    if id is None:
        g.rodzic = None
    else:
        g.rodzic = db.execute(
            'SELECT * FROM rodzice WHERE id = ?',
            (id,)
        ).fetchone()

def auth_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.rodzic is None:
            return redirect(url_for('index'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/auth/<string:key>')
def auth(key):
    db = get_db()
    valid, id = Serializer(current_app.config['SECRET_KEY']).loads_unsafe(key)
    if not valid:
        flash('Niepoprawny hash. Sprawdź czy nie pomyliłeś się przy przepisywaniu.')
        return redirect(url_for('index'))
    rodzic = db.execute(
        'SELECT * FROM rodzice WHERE id = ?',
        (id,)
    ).fetchone()        
    if not rodzic:
        flash('Niepoprawny numer nauczyciela.')
        return redirect(url_for('index'))
    else:
        session.clear()
        session['rodzic'] = id
        return redirect(url_for('manage.panel'))

@bp.route('/', methods=('GET', 'POST'))
@auth_required
def panel():
    db = get_db()
    id = session['rodzic']
    rodzic = db.execute(
        'SELECT * FROM rodzice WHERE id = ?',
        (id,)
    ).fetchone()
    terminy = db.execute(
        'SELECT * FROM wizyty JOIN nauczyciele ON nauczyciele.id = wizyty.id_nauczyciela '
        'WHERE id_rodzica = ? ORDER BY godzina', (rodzic['id'],)
    ).fetchall()
    return render_template('zapisy/manage.html', email=rodzic['email'], terminy=terminy)

