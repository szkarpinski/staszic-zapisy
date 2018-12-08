import functools
import configparser
import click
import os
from flask import (
    Blueprint, render_template, session, redirect, url_for, current_app, request, flash
)
from flask.cli import with_appcontext
from main.db import get_db
from werkzeug.security import check_password_hash, generate_password_hash
from getpass import getpass


bp = Blueprint('admin', __name__, url_prefix='/admin')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('user') != 'admin':
            return redirect(url_for('admin.login'))

        return view(**kwargs)

    return wrapped_view


# Podstawowy interface admina
@bp.route('/', methods=('GET', 'POST'))
@login_required
def admin():
    db = get_db()
    if request.method == 'POST':
        pass

    #Lista nauczycieli
    nauczyciele = db.execute(
        'SELECT id, imie, nazwisko, email, obecny FROM nauczyciele'
    ).fetchall()

    #Opcje
    conf = configparser.ConfigParser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))
    
    
    return render_template('admin/panel.html', nauczyciele = nauczyciele)

#Interfejs ustawień - szczegóły nauczyciela
@bp.route('/nauczyciel/<int:id>', methods=('GET', 'POST'))
@login_required
def admin_nauczyciel(id):
    db = get_db()
    if request.method == 'POST':
        pass

    #Lista zapisów dla nauczyciela
    terminy = db.execute(
        'SELECT imie_ucznia, nazwisko_ucznia, imie_rodzica, nazwisko_rodzica, godzina '
        'FROM wizyty WHERE id = ?', (id,)
    ).fetchall()
    nauczyciel = db.execute(
        'SELECT imie, nazwisko, email, obecny FROM nauczyciele WHERE id = ?',(id,)
    ).fetchone()

    return render_template('admin/nauczyciel.html',
                           terminy = terminy,
                           nauczyciel = nauczyciel
    )

    
#Interfejs dodawania nauczycieli
@bp.route('/dodaj', methods=('GET', 'POST'))
@login_required
def dodaj_nauczyciela():
    db = get_db()
    if request.method == 'POST':
        imie = request.form.get('fname')
        nazwisko = request.form.get('lname')
        email  = request.form.get('email')
        obecny = request.form.get('present')
        error = None

        if not imie:
            error = "Brakuje imienia nauczyciela."
        elif not nazwisko:
            error = "Brakuje nazwiska nauczyciela."
        elif not email:
            error = "Brakuje adresu e-mail."

        if error is not None:
            print(error)
            flash(error)
        else:
            #dodawanie nauczyciela
            db.execute(
                'INSERT INTO nauczyciele '
                '(imie, nazwisko, email, obecny) '
                'VALUES (?, ?, ?, ?)',
                (imie, nazwisko, email, obecny) #czy można tak beztrosko "obecny"?
            )
            db.commit()
            return redirect(url_for('admin.dodaj_nauczyciela'))
        
    return render_template('admin/add.thml')

# Interface logowania
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        # username = request.method.get('username')
        password = request.form.get('password')
        conf = configparser.ConfigParser()
        conf.read(os.path.join(current_app.instance_path, 'config.ini'))
        error = None

        if not check_password_hash(conf['admin']['hash'], password):
            error = 'Nieprawidłowe hasło administratora!'

        if error is None:
            session.clear()
            session['user'] = 'admin'
            return redirect(url_for('admin.admin'))
        else:
            flash(error)

    return render_template('admin/login.html')


# Wylogowanie
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# Komenda do ustawiania hasła
@click.command('set-pw')
@with_appcontext
def set_password_command():
    conf = configparser.ConfigParser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))
    conf['admin']['hash'] = generate_password_hash(getpass('Nowe hasło: '))
    with open(os.path.join(current_app.instance_path, 'config.ini'), 'w') as confile:
        conf.write(confile)

def init_app(app):
    app.cli.add_command(set_password_command)
