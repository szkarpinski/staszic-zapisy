import functools
import datetime as dt
import configparser
import os
from flask import (
    Blueprint, render_template, current_app
)
from main.db import get_db


bp = Blueprint('zapisy', __name__)


# Index, w którym da się zobaczyć podsumowanie nauczycieli
@bp.route('/')
def index():
    db = get_db()

    # Komunikacja z bazą
    nauczyciele = db.execute(
        'SELECT id, imie, nazwisko, obecny FROM nauczyciele'
    ).fetchall()
    
    # View
    return render_template('zapisy/index.html', nauczyciele=nauczyciele)
    
# View wyboru godziny do zapisu (tu trzeba będzie dopisać jakieś POSTy)
@bp.route('/nauczyciel/<int:id>')
def nauczyciel(id):
    db = get_db()

    # Komunikacja z bazą
    zajete = db.execute(
        'SELECT godzina FROM wizyty WHERE id_nauczyciela = ?', (id,)
    ).fetchall()
    zajete = [dt.datetime.strptime(
        conf['dzien otwarty']['data'] + ' ' + r['godzina'], '%d/%m/%Y %H:%M')
        for r in zajete]
    dane_nauczyciela = db.execute(
        'SELECT imie, nazwisko FROM nauczyciele WHERE id = ?', (id,)
    ).fetchone()
    if dane_nauczyciela is None:
        return 'Nauczyciel not found :('
    # print (dane_nauczyciela['imie'], dane_nauczyciela['nazwisko'])
    
    # Ustawienie wszystkich dat
    conf = configparser.ConfigParser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))
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

