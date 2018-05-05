import requests
from functools import wraps
from flask import request, Response


def check_auth(username, password):
    with open("./processors/password.txt", "r") as password_file:
        user_password = password_file.read()
    return username == 'admin' and password == user_password


def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', requests.codes.unauthorized,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated
