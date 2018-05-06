import requests
from flask import Blueprint, render_template, Response
from werkzeug.exceptions import abort

from app.auth import requires_auth
from app.info import available_devices

router = Blueprint('router', __name__, template_folder='templates')


@router.route('/')
@router.route('/home/')
@requires_auth
def home():
    return render_template('home.html', devices=available_devices())


@router.route('/devices/<device_id>')
@requires_auth
def device(device_id):
    try:
        int(device_id)
    except ValueError:
        abort(Response(status=requests.codes.bad_request, response="Invalid device id specified."))

    devices = available_devices()
    if int(device_id) < 0:
        abort(Response(status=requests.codes.not_found, response="Device not found."))
    for dev in devices:
        if dev.keys()[0] == device_id:
            break
    else:
        abort(Response(status=requests.codes.not_found, response="Device not found."))

    # config = database.get_config_of_camera()
    # add config to template
    return render_template('device.html', device_id=device_id)


@router.route('/devices/<device_id>/content')
@requires_auth
def content():
    return render_template('content.html')


@router.route('/login/')
def login():
    return render_template('login.html')


@router.route('/register/')
def register():
    return render_template('register.html')


@router.route('/help/')
def help():
    return render_template('help.html')


@router.route('/documentation/')
@requires_auth
def documentation():
    return render_template('documentation.html')
