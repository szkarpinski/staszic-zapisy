import datetime as dt
import configparser
import os
import re
from itsdangerous import Serializer
from flask import (
    Blueprint, render_template, current_app, request, url_for, make_response, flash, redirect
)
from main import mail
from main.db import get_db
from werkzeug.exceptions import abort
import _thread
from . import captcha

bp = Blueprint('zapisy', __name__)


# Index, w którym da się zobaczyć podsumowanie nauczycieli
@bp.route('/')
def index():
    db = get_db()
    conf = configparser.ConfigParser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))

    # Komunikacja z bazą
    nauczyciele = db.execute(
        'SELECT id, imie, nazwisko, obecny FROM nauczyciele ORDER BY nazwisko, imie'
    ).fetchall()

    # Semafor pokazywania, ze mail zostal wyslany
    success = request.args.get('show_success')
    if success:
        pass
    else:
        success = 0

    # Opcjonalne ogłoszenie
    ogloszenie = ''
    if conf['ogloszenie']['pokaz'] != str(0):
        ogloszenie = conf['ogloszenie']['tresc']
    
    # View
    return render_template('zapisy/index.html', nauczyciele=nauczyciele,
                           show_success=int(success),
                           ogloszenie=ogloszenie
    )
    
# View wyboru godziny do zapisu
@bp.route('/nauczyciel/<int:id>', methods=('GET', 'POST'))
def nauczyciel(id):
    db = get_db()
    conf = configparser.ConfigParser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))

    dane_nauczyciela = db.execute(
        'SELECT imie, nazwisko, obecny FROM nauczyciele WHERE id = ?', (id,)
    ).fetchone()

    # Przetwarzanie zapytania (rezerwacji godziny)
    if request.method == 'POST':
        imie_ucznia = request.form.get('sfname')
        nazwisko_ucznia = request.form.get('slname')
        imie_rodzica = request.form.get('pfname')
        nazwisko_rodzica = request.form.get('plname')
        email = request.form.get('email')
        godzina = request.form.get('hour')
        rodo = request.form.get('rodo')
        error = None
        captcha_response = request.form.get('g-recaptcha-response')

        if not imie_ucznia:
            error = "Brakuje imienia ucznia."
        elif not nazwisko_ucznia:
            error = "Brakuje nazwiska ucznia."
        elif not imie_rodzica:
            error = "Brakuje imienia rodzica."
        elif not nazwisko_rodzica:
            error = "Brakuje nazwiska rodzica."
        elif not email:
            error = "Brakuje adresu e-mail."
        elif not rodo:
            error = "Brakuje zgody na przetwarzanie danych osobowych."
        elif not godzina or not re.match('[0-2]?\d:[0-5]\d', godzina) or godzina != re.match('[0-2]\d:[0-5]\d', godzina).group(0):
            error = "Godzina jest w nieodpowiednim formacie."
        #google reCAPTCHA
        elif int(conf['captcha']['use_captcha'])==1 \
            and not captcha.checkRecaptcha(captcha_response):
                error = "Okropny z ciebie bot!!!"
        # Trzeba zrobić jakoś transakcje
        elif not dane_nauczyciela['obecny']:
            error = 'Nauczyciel nie będzie obecny na dniu otwartym.'
        else:
            if db.execute('SELECT * FROM wizyty '
                          'WHERE id_nauczyciela = ? AND godzina = ?',
                          (id, godzina)).fetchone() is not None:
                error = 'Godzina jest już zajęta.'


        if error is not None:
            print(error)
            flash(error)
        else:          
            # Rezerwowanie terminu
            # Zapis rodzica
            rodzic = db.execute(
                'SELECT * FROM rodzice '
                'WHERE imie = ? AND nazwisko = ? AND imie_ucznia = ? AND nazwisko_ucznia = ? AND email = ?',
                (imie_rodzica, nazwisko_rodzica, imie_ucznia, nazwisko_ucznia, email)
            ).fetchone()
            if not rodzic:
                db.execute(
                    'INSERT INTO rodzice '
                    '(imie, nazwisko, imie_ucznia, nazwisko_ucznia, email) '
                    'VALUES (?, ?, ?, ?, ?)',
                    (imie_rodzica, nazwisko_rodzica, imie_ucznia, nazwisko_ucznia, email)
                )
                rodzic = db.execute(
                    'SELECT * FROM rodzice '
                    'WHERE imie = ? AND nazwisko = ? AND imie_ucznia = ? AND nazwisko_ucznia = ? AND email = ?',
                    (imie_rodzica, nazwisko_rodzica, imie_ucznia, nazwisko_ucznia, email)
                ).fetchone()
            db.execute(
                'INSERT INTO wizyty '
                '(id_nauczyciela, id_rodzica, godzina)'
                ' VALUES (?, ?, ?)',
                (id, rodzic['id'], godzina)
            )
            db.commit()
            
            # Wysyłanie maila potwierdzającego
            mail.send_message(
                subject='Dzień otwarty {}'.format(conf['dzien otwarty']['data']),
                html=render_template('email/potwierdzenie.html',
                                     pfname=imie_rodzica,
                                     plname=nazwisko_rodzica,
                                     sfname=imie_ucznia,
                                     slname=nazwisko_ucznia,
                                     hour=godzina,
                                     date=conf['dzien otwarty']['data'],
                                     dane_nauczyciela=dane_nauczyciela,
                                     link=url_for('manage.auth', key=Serializer(current_app.config['SECRET_KEY']).dumps(rodzic['id']), _external=True),
                ),
                recipients=[email]
            )
            #todo: handle & log errors

            return redirect(url_for('index', show_success=1))

    # Ustawienie wszystkich dat
    start = dt.datetime.strptime(
        conf['dzien otwarty']['data'] + ' ' + conf['dzien otwarty']['start'],
        '%d/%m/%Y %H:%M'
    )
    koniec = dt.datetime.strptime(
        conf['dzien otwarty']['data'] + ' ' + conf['dzien otwarty']['koniec'],
        '%d/%m/%Y %H:%M'
    )
    blok = conf['dzien otwarty']['blok']
    blok = [int(s) for s in blok.split(':')]
    blok = dt.timedelta(hours=blok[0], minutes=blok[1])

    # Komunikacja z bazą
    zajete = db.execute(
        'SELECT godzina FROM wizyty WHERE id_nauczyciela = ?', (id,)
    ).fetchall()
    zajete = [dt.datetime.strptime(
        conf['dzien otwarty']['data'] + ' ' + r['godzina'], '%d/%m/%Y %H:%M')
        for r in zajete]
    if dane_nauczyciela is None:
        abort(404, 'Nauczyciel o podanym ID {0} nie znaleziony :(('.format(id))
    elif not dane_nauczyciela['obecny']:
        abort(404,
              'Nauczyciel o podanym ID {0} '
              'nie będzie obecny na dniu otwartym. :(('.format(id))

    # Liczenie wolnych godzin
    rozklad = []
    t = start
    while t < koniec:
        if t in zajete:
            rozklad.append({'start':t, 'koniec':t + blok, 'wolne':False})
        else:
            rozklad.append({'start':t, 'koniec':t + blok, 'wolne':True})
        t += blok

    return render_template('zapisy/nauczyciel.html',
                           rozklad=rozklad,
                           imie=dane_nauczyciela['imie'],
                           nazwisko=dane_nauczyciela['nazwisko'],
                           use_captcha=conf['captcha']['use_captcha'],
                           captcha_sitekey=conf['captcha']['captcha_sitekey'],
    )

