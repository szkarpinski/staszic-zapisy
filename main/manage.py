import configparser
import functools
from itsdangerous import Serializer, BadSignature
from main.db import get_db
from flask import (
    Blueprint, render_template, flash, redirect, url_for, session, g, current_app, request
)
from main.db import get_db


bp = Blueprint('manage', __name__, url_prefix='/manage')


@bp.before_app_request
def load_parent():
    db = get_db()
    id = session.get('rodzic', None)

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
        flash('Rodzic pasujący do hasha nie istnieje. ')
        return redirect(url_for('index'))
    else:
        session.clear()
        session['rodzic'] = id
        return redirect(url_for('manage.panel'))

@bp.route('/', methods=('GET', 'POST'))
@auth_required
def panel():
    db = get_db()
    terminy = db.execute(
        'SELECT * FROM wizyty JOIN nauczyciele ON nauczyciele.id = wizyty.id_nauczyciela '
        'WHERE id_rodzica = ? ORDER BY godzina', (g.rodzic['id'],)
    ).fetchall()
    return render_template('zapisy/manage.html',
                           terminy=terminy,
    )

@bp.route('/delet', methods=['POST'])
@auth_required
def delet():
    db = get_db()
    godzina = request.form['godzina']
    id_nauczyciela = request.form['id_nauczyciela']
    wizyta = db.execute(
        'SELECT * FROM wizyty '
        'WHERE id_nauczyciela = ? '
        'AND godzina = ?',
        (id_nauczyciela, godzina)
    ).fetchone()
    if not wizyta:
        flash('Nie ma takiej wizyty.')
        return redirect(url_for('manage.panel'))
    if wizyta['id_rodzica'] != g.rodzic['id']:
        flash('To nie twoja wizyta.')
        return redirect(url_for('manage.panel'))
    db.execute(
        'DELETE FROM wizyty '
        'WHERE id_nauczyciela = ? '
        'AND godzina = ?',
        (id_nauczyciela, godzina))
    db.commit() #commit(die)
    return redirect(url_for('manage.panel'))
