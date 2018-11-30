import functools
from copy import deepcopy
import datetime as dt
import configparser
from flask import (
    Blueprint, render_template)
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
    

'''
    rozklad = {}
    for (idn, trash, trash) in nauczyciele:
        rozklad[idn] = []
        t = deepcopy(start)
        while t < koniec:


            
# Ustawienie wszystkich dat
    conf = configparser.ConfigParser()
    conf.read('./config.ini')
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

zajete = db.execute(
        'SELECT id_nauczyciela, godzina FROM wizyty'
    ).fetchall()
    '''
