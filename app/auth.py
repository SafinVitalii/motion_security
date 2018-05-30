from functools import wraps

from bcrypt import hashpw, gensalt
from flask import request, session
from werkzeug.utils import redirect

from app.info import is_browser_request
from app.token import AuthToken
from models.model import Model

tokens = []


def get_or_create_token(email):
    if not tokens or not [email for token in tokens if token.email == email]:
        t = AuthToken(email)
        tokens.append(t)
        return t.token
    else:
        t = [token for token in tokens if token.email == email][0]
        return t.token


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if is_browser_request():
            try:
                session['user']
            except KeyError:
                return redirect('/login')
            if not session['user']:
                return redirect('/login')
            return f(*args, **kwargs)
        elif not request.headers.environ.get('HTTP_AUTH_TOKEN'):
            return 'No Auth-Token header specified', 401
        else:
            if not verify_token():
                return 'Invalid Auth-Token specified. Pleas use /login endpoint to login', 401
            return f(*args, **kwargs)

    return decorated_function


def verify_password(email, password):
    user = Model(table='users').read(email)
    if not user or not hashpw(password, str(user[0][1])) == user[0][1]:
        return False
    session['user'] = user[0][2]
    return True


def verify_token():
    token = request.headers.environ.get('HTTP_AUTH_TOKEN')
    if not tokens or not [t for t in tokens if t.token == token]:
        return False
    return True


def encrypt(password):
    return hashpw(password, gensalt())
