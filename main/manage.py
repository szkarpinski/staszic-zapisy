import configparser
from flask import (
    Blueprint, render_template, flash
)
from main.db import get_db

bp = Blueprint('manage', __name__)

@bp.route('/manage/<string:key>', methods=('GET', 'POST'))
def panel(key):
    db = get_db()

    return rander_template('zapisy/manage.html')

