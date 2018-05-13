from functools import wraps

from bcrypt import hashpw, gensalt
from flask import session
from werkzeug.utils import redirect

from models.model import Model


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            session['user']
        except KeyError:
            return redirect('/login')
        if not session['user']:
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated_function


def verify_password(email, password):
    user = Model(table='users').read(email)
    if not user or not hashpw(password, str(user[0][1])) == user[0][1]:
        return False
    session['user'] = user[0][2]
    return True


def encrypt(password):
    return hashpw(password, gensalt())
