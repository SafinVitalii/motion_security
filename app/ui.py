import re
import requests

from email.utils import parseaddr
from flask import Blueprint, render_template, Response, request
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from app.auth import requires_auth
from app.info import available_devices
from processors.monitor import Monitor

router = Blueprint('router', __name__, template_folder='templates')


@router.route('/')
@router.route('/index/')
def index():
    return render_template('index.html')


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
    return render_template('device.html', device_id=device_id,
                           content_url='/devices/{}/content/'.format(int(device_id)))


@router.route('/devices/<device_id>/content/')
@requires_auth
def content(device_id):
    return render_template('content.html', video_url='/devices/{}/video/'.format(int(device_id)))


@router.route('/devices/<int:device_id>/video/')
@requires_auth
def video(device_id):
    """Video streaming route. Put this in the src attribute of an img tag."""
    monitor = Monitor(webcam_id=int(device_id), subscribers=[], streaming=True)
    return Response(monitor.stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@router.route('/login/')
def login():
    return render_template('login.html')


@router.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = request.form

        error_msg = None
        if not form.get('email') or not form.get('password'):
            error_msg = 'Both email and password are required!'
        elif parseaddr(form.get('email'))[1] == '':
            error_msg = 'Invalid email! Please try again.'
        elif len(form.get('password')) < 8:
            error_msg = 'Make sure your password is at least 8 letters.'
        elif not re.search('[0-9]', form.get('password')):
            error_msg = 'Make sure your password has a number in it.'
        elif not re.search('[A-Z]', form.get('password')):
            error_msg = 'Make sure your password has a capital letter in it.'

        if error_msg:
            return render_template(
                'register.html', error=error_msg, email=form.get('email'),
                password=form.get('password')
            ), requests.codes.bad_request

        # save to db
        return redirect('/index')
    else:
        return render_template('register.html')


@router.route('/help/')
def help():
    return render_template('help.html')


@router.route('/documentation/')
@requires_auth
def documentation():
    return render_template('documentation.html')
