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


    rodzice = db.execute('SELECT email_rodzica '
                         'FROM wizyty '
                         'GROUP BY email_rodzica').fetchall()
    for rodzic in rodzice:
        rodzic = rodzic['email_rodzica']
        wizyty = db.execute('SELECT * '
                            'FROM wizyty w JOIN nauczyciele n '
                            'ON n.id=w.id_nauczyciela '
                            'WHERE w.email_rodzica = ?',
                            (rodzic,)
                 ).fetchall()

        mail.send_message(
            subject='Podsumowanie zapisów na dzień otwarty {}'.format(conf['dzien otwarty']['data']),
            html=render_template('email/podsumowanie_rodzic.html',
                                 wizyty=wizyty),
            recipients=[rodzic],
        )
    
    nauczyciele = db.execute('SELECT * FROM nauczyciele')
    for nauczyciel in nauczyciele:
        wizyty = db.execute('SELECT * FROM wizyty WHERE id_nauczyciela = ?',
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
