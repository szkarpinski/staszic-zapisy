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
    dane_ogloszen = conf['ogloszenie']

    if request.method == 'POST':
        date = request.form.get('date')
        start = request.form.get('start')
        end = request.form.get('end')
        interval = request.form.get('interval')
        uzyj_ogloszenia = True #request.form.get(' ')
        tresc_ogloszenia = "Numery sal pierdu pierdu" #request.form.get('  ')
        message = "Ustawiono: "
        print(date, start, end, interval)

        zmieniono = False
        if date:
            message += "datę, "
            dane_dnia['data'] = date.replace('.', '/')
            zmieniono = True
        if start:
            if start > (end if end else dane_dnia['koniec']):
                message += 'początek (zła wartość), '
            else:
                message += "początek, "
                dane_dnia['start'] = start
                zmieniono = True
        if end:
            if end < dane_dnia['start']:
                message += 'koniec (zła wartość), '
            else:
                message += "koniec, "
                dane_dnia['koniec'] = end
                zmieniono = True
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
                zmieniono = True
        if uzyj_ogloszenia:
            message += "widoczność ogłoszenia, "
            dane_ogloszen['pokaz'] = uzyj_ogloszenia
            zmieniono = True
        if tresc_ogloszenia:
            message += "treść ogłoszenia, "
            dane_ogloszen['tresc'] = tresc_ogloszenia
            zmieniono = True
        
        if message == "Ustawiono: ":
            message = "Nic nie zmieniono"
        else:
            message = message[:-2]
            with open(os.path.join(current_app.instance_path,
                                   'config.ini'), 'w') as confile:
                conf.write(confile)
        print(message)
        flash(message)

        # Reset bazy wizyt po zmianie danych czasowych
        if zmieniono:
            db.execute('DELETE FROM wizyty')
            db.execute('UPDATE nauczyciele SET obecny = 1')
            db.commit()

    #Lista nauczycieli
    nauczyciele = db.execute(
        'SELECT id, imie, nazwisko, email, obecny FROM nauczyciele'
    ).fetchall()

    ustawienia_czasu = {}
    ustawienia_czasu['date'] = dane_dnia['data'].replace('/', '.')
    ustawienia_czasu['start'] = dane_dnia['start']
    ustawienia_czasu['end'] = dane_dnia['koniec']

    def minutes(hm):
        return int(hm.split(':')[0])*60+int(hm.split(':') [1])
    ustawienia_czasu['interval'] = minutes(dane_dnia['blok'])

    uzyj_ogloszenia = dane_ogloszen['pokaz']
    tresc_ogloszenia = dane_ogloszen['tresc']
        
    return render_template('admin/panel.html',
                           nauczyciele = nauczyciele,
                           ustawienia_czasu=ustawienia_czasu,
                           pokaz_ogloszenie=uzyj_ogloszenia,
                           ogloszenie=tresc_ogloszenia
    )

#Interfejs ustawień - szczegóły nauczyciela
@bp.route('/nauczyciel/<int:id>', methods=('GET', 'POST'))
@login_required
def nauczyciel(id):
    db = get_db()
    if request.method == 'POST':
        print("POST osiagniety")
        
        if request.form.get('delete') == 'true':
            db.execute('DELETE FROM wizyty WHERE id_nauczyciela = ?', (id,))
            db.execute('DELETE FROM nauczyciele WHERE id = ?', (id,))
            db.commit()
            return redirect(url_for('admin.admin'))
        
        imie = request.form.get('fname')
        nazwisko = request.form.get('lname')
        email = request.form.get('email')
        obecny = request.form.get('present')
        # print(imie, nazwisko, email, obecny, request.form.get('delete'))
        error = None
        if imie is None:
            error = 'Puste imie.'
        elif nazwisko is None:
            error = 'Puste nazwisko.'
        elif email is None:
            error = 'Pusty email.'
        
        if error is not None:
            flash(error)
            print("błąd:"+error)
        else:
            db.execute('UPDATE nauczyciele '
                       'SET imie = ?, nazwisko = ?, email = ?, obecny = ? '
                       'WHERE id = ?',
                       (imie, nazwisko, email, 1 if obecny=='on' else 0, id))
            db.commit()
            print("Zmieniono")

    #Lista zapisów dla nauczyciela
    terminy = db.execute(
        'SELECT imie_ucznia, nazwisko_ucznia, imie_rodzica, nazwisko_rodzica, godzina '
        'FROM wizyty WHERE id_nauczyciela = ? ORDER BY godzina', (id,)
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
                (imie, nazwisko, email, 1 if obecny=='on' else 0)
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
        print(conf['admin']['hash'])
        
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
