import functools
import configparser
import click
import os
import datetime as dt
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
    conf = configparser.ConfigParser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))
    dane_dnia = conf['dzien otwarty']

    if request.method == 'POST':
        date = request.form.get('date')
        start = request.form.get('start')
        end = request.form.get('end')
        interval = request.form.get('interval')
        message = "Ustawiono: "
        print(date, start, end, interval)
        
        if date:
            message += "datę, "
            dane_dnia['data'] = date.replace('.', '/')
        if start:
            if start > (end if end else dane_dnia['koniec']):
                message += 'początek (zła wartość), '
            else:
                message += "początek, "
                dane_dnia['start'] = start
        if end:
            if end < dane_dnia['start']:
                message += 'koniec (zła wartość), '
            else:
                message += "koniec, "
                dane_dnia['koniec'] = end
        if interval:
            interval = int(interval)
            duration = dt.datetime.strptime(
                         dane_dnia['data'] +
                         dane_dnia['koniec'],
                         '%d/%m/%Y%H:%M') - \
                       dt.datetime.strptime(
                         dane_dnia['data'] +
                         dane_dnia['start'],
                         '%d/%m/%Y%H:%M')
            if interval <= 0 or interval > duration.seconds / 60:
                message += "czas trwania spotkania (zła wartość), "
            else:
                message += "czas trwania spotkania, "
                dane_dnia['blok'] = "{}:{}".format(
                    int(interval) // 60, int(interval) % 60)
            
        if message == "Ustawiono: ":
            message = "Nic nie zmieniono"
        else:
            message = message[:-2]
            with open(os.path.join(current_app.instance_path,
                                   'config.ini'), 'w') as confile:
                conf.write(confile)
        print(message)
        flash(message)

    #Lista nauczycieli
    nauczyciele = db.execute(
        'SELECT id, imie, nazwisko, email, obecny FROM nauczyciele'
    ).fetchall()

    ustawienia_czasu = {}
    ustawienia_czasu['date'] = dane_dnia['data'].replace('/', '.')
    ustawienia_czasu['start'] = dane_dnia['start']
    ustawienia_czasu['end'] = dane_dnia['koniec']
    ustawienia_czasu['interval'] = dane_dnia['blok']

    return render_template('admin/panel.html', nauczyciele = nauczyciele, ustawienia_czasu=ustawienia_czasu)

#Interfejs ustawień - szczegóły nauczyciela
@bp.route('/nauczyciel/<int:id>', methods=('GET', 'POST'))
@login_required
def nauczyciel(id):
    db = get_db()
    if request.method == 'POST':
        #TODO po zrobieniu templatea
        pass

    #Lista zapisów dla nauczyciela
    terminy = db.execute(
        'SELECT imie_ucznia, nazwisko_ucznia, imie_rodzica, nazwisko_rodzica, godzina '
        'FROM wizyty WHERE id_nauczyciela = ?', (id,)
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
        
    return render_template('admin/add.html')

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
