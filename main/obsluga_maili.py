import configparser
import click
from flask import render_template
from main.db import get_db
from main import mail


# Komenda do wywołania przez crona
@click.command('send-mail')
def send_mails():
    db = get_db()
    conf = configparser.Configparser()
    conf.read(os.path.join(current_app.instance_path, 'config.ini'))


    rodzice = db.execute('SELECT email_rodzica '
                         'FROM wizyty '
                         'GROUP BY email_rodzica').fetchall()
    for rodzic in rodzice:
        rodzic = rodzic['email']
        wizyty = db.execute('SELECT * '
                            'FROM wizyty w JOIN nauczyciele n '
                            'ON n.id=w.id_nauczyciela '
                            'WHERE w.email_rodzica = ?',
                            (rodzic,)
                 ).fetchall()

        mail.send_message(
            subject='Podsumowanie zapisów na dzień otwarty {}'.format(conf['dzien otwarty']['data']),
            html=render_template('email/podsumowanie_rodzic.html',
                                 wizyty=wizyty)),
            recipients=[rodzic]
        )
    
    nauczyciele = db.execute('SELECT * FROM nauczyciele')
    for nauczyciel in nauczyciele:
        wizyty = db.execute('SELECT * FROM wizyty WHERE id_nauczyciela = ?',
                            (nauczyciel['id'],))
        mail.send_message(
            subject='Pdsumowanie zapisów na dzień otwarty {}'.format(conf['dzien otwarty']['data']),
            html=render_template('email/podsumowanie_nauczyciel.html',
                                 wizyty=wizyty)
            recipients=[nauczyciel['email']]
        )


def init_app(app):
    app.cli.add_command(send_mail)
