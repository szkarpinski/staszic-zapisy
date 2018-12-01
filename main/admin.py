import functools
import configparser
import click
import os
from flask import (
    Blueprint, render_template, session, redirect, url_for, current_app
)
from flask.cli import with_appcontext
from main.db import get_db
from werkzeug.security import check_password_hash, generate_password_hash
from getpass import getpass


bp = Blueprint('admin', __name__, url_prefix='/admin')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin.login'))

        return view(**kwargs)

    return wrapped_view


# Podstawowy interface admina
@bp.route('/', methods=('GET', 'POST'))
@login_required
def admin():
    return '2137 XD'


# Interface logowania
@bp.route('/login', methods=('GET', 'POST'))
def login():
    return 'JP2GMD XD'


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
