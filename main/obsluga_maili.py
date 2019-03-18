import configparser
import click
import sqlite3
import os
from flask import render_template, current_app
from flask.cli import with_appcontext
from main import mail


# Komenda do wywołania przez crona
@click.command('send-mail')
@with_appcontext
def send_mails():
    db = sqlite3.connect(os.path.join(current_app.instance_path, 'main.sqlite'))
    db.row_factory = sqlite3.Row
    conf = configparser.ConfigParser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))


    rodzice = db.execute('SELECT rodzice.email AS email_rodzica '
                         'FROM wizyty JOIN rodzice ON wizyty.id_rodzica = rodzice.id '
                         'GROUP BY email_rodzica').fetchall()
    for rodzic in rodzice:
        rodzic = rodzic['email_rodzica']
        wizyty = db.execute('SELECT * '
                            'FROM wizyty w JOIN nauczyciele n '
                            'ON n.id=w.id_nauczyciela '
                            'JOIN rodzice r ON r.id=w.id_rodzica '
                            'WHERE r.email = ? AND obecny = 1',
                            (rodzic,)
                 ).fetchall()

        mail.send_message(
            subject='Podsumowanie zapisów na dzień otwarty {}'.format(conf['dzien otwarty']['data']),
            html=render_template('email/podsumowanie_rodzic.html',
                                 wizyty=wizyty),
            recipients=[rodzic],
        )
    
    nauczyciele = db.execute('SELECT * FROM nauczyciele WHERE obecny = 1')
    for nauczyciel in nauczyciele:
        wizyty = db.execute('SELECT imie_ucznia, nazwisko_ucznia, godzina, '
                            'rodzice.imie AS imie_rodzica, rodzice.nazwisko AS nazwisko_rodzica '
                            'FROM wizyty JOIN rodzice ON wizyty.id_rodzica = rodzice.id '
                            'WHERE id_nauczyciela = ?',
                            (nauczyciel['id'],)).fetchall()
        if nauczyciel['email'] != '?' and wizyty:
            mail.send_message(
                subject='Podsumowanie zapisów na dzień otwarty {}'.format(conf['dzien otwarty']['data']),
                html=render_template('email/podsumowanie_nauczyciel.html',
                                     wizyty=wizyty),
                recipients=[nauczyciel['email']],
            )


def init_app(app):
    app.cli.add_command(send_mails)
