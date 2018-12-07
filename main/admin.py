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
@bp.route('/admin', methods=('GET', 'POST'))
@login_required
def admin():
    if request.method == 'POST':
        if request.form['submitbtn'] == "delteacher":
            pass
        elif request.form['submitbtn'] == "addteacher":
            pass
        elif request.form['submitbtn'] == "modifyteacher":
            pass
        elif request.form['submitbtn'] == "modifysettings":
            pass
        elif request.form['submitbtn'] == "sendmail_close":
            pass
    return render_template('admin/panel.html')


# Interface logowania
@bp.route('/admin/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        # username = request.method.get('username')
        password = request.method.get('password')
        conf = configparser.ConfigParser()
        conf.read(os.path.join(current_app.instance_path, 'config.ini'))
        # error = None
        if not check_password_hash(conf['admin']['hash'], password):
            error = 'Nieprawidłowe hasło daministratora!'

        if error is None:
            session.clear()
            session['user'] = 'admin'
            return redirect(url_for('index'))
        flash(error)
    return render_template('admin/login.html')


# Wylogowanie
@bp.route('/admin/logout')
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
