import datetime as dt
import configparser
import os
from flask import (
    Blueprint, render_template, current_app, request, url_for, make_response, flash, redirect
)
from main import mail
from main.db import get_db
from werkzeug.exceptions import abort
import _thread

bp = Blueprint('zapisy', __name__)


# Index, w którym da się zobaczyć podsumowanie nauczycieli
@bp.route('/')
def index():
    db = get_db()

    # Komunikacja z bazą
    nauczyciele = db.execute(
        'SELECT id, imie, nazwisko, obecny FROM nauczyciele'
    ).fetchall()
    
    # View
    return render_template('zapisy/index.html', nauczyciele=nauczyciele)
    
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
        error = ''

        if not imie_ucznia:
            error += "Brakuje imienia ucznia."
        elif not nazwisko_ucznia:
            error += "Brakuje nazwiska ucznia."
        elif not imie_rodzica:
            error += "Brakuje imienia rodzica."
        elif not nazwisko_rodzica:
            error += "Brakuje nazwiska rodzica."
        elif not email:
            error += "Brakuje adresu e-mail."
        elif not rodo:
            error += "Brakuje zgody na przetwarzanie danych osobowych."
        # Trzeba zrobić jakoś transakcje
        elif not dane_nauczyciela['obecny']:
            error = 'Nauczyciel nie będzie obecny na dniu otwartym.'
        else:
            if db.execute('SELECT * FROM wizyty '
                          'WHERE id_nauczyciela = ? AND godzina = ?',
                          (id, godzina)).fetchone() is not None:
                error = 'Godzina jest już zajęta.'


        if error:
            print(error)
            flash(error)
        else:          
            # Rezerwowanie terminu
            db.execute(
                'INSERT INTO wizyty '
                '(id_nauczyciela, imie_rodzica, nazwisko_rodzica, email_rodzica, '
                'imie_ucznia, nazwisko_ucznia, godzina)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (id, imie_rodzica, nazwisko_rodzica, email, imie_ucznia, nazwisko_ucznia, godzina)
            )
            db.commit()
            
            # Wysyłanie maila potwierdzającego
            def send_mail(app):
                with app.app_context():
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
                        ),
                        recipients=[email]
                    )
                #todo: handle & log errors

            _thread.start_new_thread(send_mail, (current_app._get_current_object(),))

            return redirect(url_for('index'))

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
    )

