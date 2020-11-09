from flask import Blueprint, render_template
from flask import request, flash, redirect, url_for
from flask_login import login_required, logout_user, login_user, current_user

bp = Blueprint('detection', __name__, template_folder='../templates')


@bp.route('/', methods=['GET', 'POST'])
def home():

    return render_template('home.html')