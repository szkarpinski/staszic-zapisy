import configparser
from flask import Blueprint, render_temaplate
from main.db import db


bp = Blueprint('admin', __name__, url_prefix='/admin')
