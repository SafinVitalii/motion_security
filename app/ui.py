import requests
from flask import Blueprint, render_template, Response
from werkzeug.exceptions import abort

from app.auth import requires_auth
from app.info import available_devices

home_page = Blueprint('home_page', __name__, template_folder='templates')
device_page = Blueprint('device_page', __name__, template_folder='templates')


@home_page.route('/')
@home_page.route('/home/')
@requires_auth
def home():
    return render_template('home.html', devices=available_devices())


@home_page.route('/devices/<device_id>')
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
