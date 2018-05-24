import re
from email.utils import parseaddr

from app.auth import verify_password
from models.model import Model


def validate_registration_form(form):
    """ /register/ endpoint"""
    error_msg = None
    if not form.get('email') or not form.get('password'):
        error_msg = 'Both email and password are required!'
    elif parseaddr(form.get('email'))[1] == '':
        error_msg = 'Invalid email! Please try again.'
    elif Model(table='users').read(form.get('email')):
        error_msg = 'User with such email already exists.'
    elif len(form.get('password')) < 8:
        error_msg = 'Make sure your password is at least 8 letters.'
    elif not re.search('[0-9]', form.get('password')):
        error_msg = 'Make sure your password has a number in it.'
    elif not re.search('[A-Z]', form.get('password')):
        error_msg = 'Make sure your password has a capital letter in it.'

    return error_msg


def validate_login_form(form):
    """ /login/ endpoint """
    error_msg = None

    if not form.get('email') or not form.get('password'):
        error_msg = 'Both email and password are required!'

    email = form.get('email')
    password = str(form.get('password'))
    result = verify_password(email, password)

    if not result:
        error_msg = 'Error occured when logging in. Please verify your credentials.'

    return error_msg
