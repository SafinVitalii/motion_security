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
    elif not isinstance(form.get('email'), str) and not isinstance(form.get('email'), unicode):
        error_msg = 'Email should be string.'
    elif not isinstance(form.get('password'), str) and not isinstance(form.get('password'), unicode):
        error_msg = 'Password should be string.'
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


def validate_config_form(form):
    """ /devices/<id>/configuration/ endpoint """
    error_msg = None

    if not form.get('subscribers') or not form.get('fps') or not form.get('duration'):
        error_msg = 'All fields are required! (subscribers, fps, duration).'

    elif not isinstance(form.get('subscribers'), str) \
            and not isinstance(form.get('subscribers'), unicode):
        error_msg = 'Subscribers should be comma-separated string.'

    else:
        try:
            str(form.get('subscribers'))
            subscribers = form.get('subscribers').split(',')
        except:
            error_msg = 'Invalid email(s) specified for subscribers section.'
        for email in subscribers:
            if parseaddr(email)[1] == '':
                error_msg = 'Invalid email(s) specified for subscribers section.'

        if not error_msg:
            if not isinstance(form.get('duration'), int):
                error_msg = 'Duration should be int.'
            elif form.get('duration') < 0 or form.get('duration') > 60:
                error_msg = 'Duration should be in range [0, 60].'

        if not error_msg:
            if not isinstance(form.get('fps'), float):
                error_msg = 'Fps should be float.'
            elif form.get('fps') < 1 or form.get('fps') > 120:
                error_msg = 'Fps should be in range [1, 120].'

    return error_msg
