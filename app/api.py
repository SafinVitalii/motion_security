import itertools

import datetime
import json
import threading

import requests
from flask import Blueprint, render_template, Response, request, session, send_from_directory
from werkzeug.exceptions import abort
from werkzeug.utils import redirect
from collections import OrderedDict
from app.auth import encrypt, login_required, get_or_create_token
from app.info import available_devices, is_browser_request
from models.model import Model
from processors.monitor import Monitor, STATUS_LIVE, STATUS_PROVISIONING, STATUS_AVAILABLE
from validators.validators import validate_registration_form, validate_login_form, \
    validate_config_form

router = Blueprint('router', __name__, template_folder='templates')


@router.route('/')
@router.route('/index/')
def index():
    """ Index page """
    if is_browser_request():
        return render_template('index.html')
    return json.dumps("Index page. Possible actions: /login, /register, /help\n")


@router.route('/home/')
@login_required
def home():
    """ Dashboard """
    from main import container
    if is_browser_request():
        return render_template('home.html', devices=container.available_devices(),
                               user=session['user'])
    return json.dumps({'devices': container.available_devices()})


@router.route('/navigation/')
@login_required
def navigation():
    """ Navigation """
    if is_browser_request():
        return render_template('navigation.html', user=session['user'])
    else:
        return json.dumps("UI specific endpoint. Nothing there."), 200


@router.route('/devices/<device_id>/')
@login_required
def device(device_id):
    """ Camera home """
    from main import container
    try:
        device_id = int(device_id)
    except ValueError:
        abort(Response(status=requests.codes.bad_request, response="Invalid device id specified."))

    devices = available_devices()
    if device_id < 0:
        abort(Response(status=requests.codes.not_found, response="Device not found."))
    for dev in devices:
        if int(dev.keys()[0]) == device_id:
            break
    else:
        abort(Response(status=requests.codes.not_found, response="Device not found."))

    # Sample config can be found in camera_config_sample.txt
    camera_config = container.d[device_id].get_config()

    resp = {
        'device_id': device_id,
        'content_url': '/devices/{}/content/'.format(device_id),
        'camera_config': camera_config,
        'status': container.d[device_id].get_status()
    }
    if is_browser_request():
        return render_template('device.html', **resp)
    resp.pop('content_url')
    return json.dumps(resp), 200


@router.route('/devices/<int:device_id>/content/')
@login_required
def content(device_id):
    """ Page for video frame """
    if not is_browser_request():
        return json.dumps("Live streaming is not available via API"), 400
    from main import container
    if container.is_monitor_available(device_id):
        container.d[device_id].set_status(STATUS_LIVE)
        return render_template('content.html',
                               video_url='/devices/{}/video/'.format(int(device_id)),
                               device_id=device_id)
    return 'Device is already in use.', 403


@router.route('/devices/<int:device_id>/video/')
@login_required
def video(device_id):
    """ Video streaming route. Put this in the src attribute of an img tag """
    if not is_browser_request():
        return json.dumps("Live streaming is not available via API"), 400
    monitor = Monitor(webcam_id=int(device_id), subscribers=[], streaming=True)
    return Response(monitor.stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@router.route('/devices/<int:device_id>/start/', methods=['POST'])
@login_required
def start(device_id):
    """ Start auto provisioning """
    from main import container
    if container.is_monitor_available(device_id):
        container.d[device_id].set_status(STATUS_PROVISIONING)
        t = threading.Thread(target=container.d[device_id].start)
        t.setDaemon(True)
        t.start()
        return '', 200
    return 'Device is already started.', 403


@router.route('/devices/<int:device_id>/stop/', methods=['POST'])
@login_required
def stop(device_id):
    """ Stop auto provisioning """
    from main import container
    if container.is_monitor_provisioning(device_id) or container.is_monitor_live(device_id):
        container.d[device_id].set_status(STATUS_AVAILABLE)
        return '', 200
    return 'Device is already stopped.', 403


@router.route('/devices/<int:device_id>/configuration/', methods=['GET', 'POST'])
@login_required
def configuration(device_id):
    """ Page for monitoring configurations """

    from main import container
    if request.method == 'POST':
        if not is_browser_request() \
                and request.headers.environ['CONTENT_TYPE'] != 'application/json':
            return json.dumps(
                "Content-Type {} is not allowed. Only application/json is allowed".format(
                    request.headers.environ['CONTENT_TYPE'])
            ), 415

        try:
            form = request.form if is_browser_request() else json.loads(request.data)
        except ValueError:
            return json.dumps('Invalid data form specified.'), 400

        error_msg = validate_config_form(form)
        if error_msg:
            resp = {
                'error': error_msg, 'subscribers': form.get('subscribers'),
                'duration': form.get('duration'), 'fps': form.get('fps')
            }
            if is_browser_request():
                return render_template('configuration.html', **resp), 400
            return json.dumps({'error': error_msg}), 400

        subscribers = form.get('subscribers').split(',')
        duration = int(form.get('duration'))
        fps = float(form.get('fps'))

        container.d[device_id].subscribers = subscribers
        container.d[device_id].default_buffer_duration = duration
        container.d[device_id].camera_fps = fps

        monitor = container.d[device_id]
        resp = {
            'subscribers': ','.join(monitor.subscribers),
            'duration': monitor.default_buffer_duration,
            'fps': monitor.camera_fps,
            'device_id': device_id,
            'success': "Configurations were changed successfully."
        }
        if is_browser_request():
            return render_template('configuration.html', **resp)
        resp.pop('success')
        return json.dumps(resp), 200

    else:
        monitor = container.d[device_id]
        resp = {
            'subscribers': ''.join(monitor.subscribers),
            'duration': monitor.default_buffer_duration,
            'fps': monitor.camera_fps,
            'device_id': device_id
        }
        if is_browser_request():
            return render_template('configuration.html', **resp), 200
        return json.dumps(resp), 200


@router.route('/login/', methods=['GET', 'POST'])
def login():
    """ Login page """
    if is_browser_request():
        if request.method == 'POST':
            form = request.form

            error_msg = validate_login_form(form)

            if error_msg:
                return render_template(
                    'login.html', error=error_msg, email=form.get('email'),
                    password=form.get('password')
                ), requests.codes.bad_request

            return redirect('/home'), requests.codes.found

        else:
            return render_template('login.html'), requests.codes.ok
    else:
        if request.method != 'POST':
            return json.dumps("GET method is not allowed for this endpoint"), 405
        elif request.headers.environ['CONTENT_TYPE'] != 'application/json':
            return json.dumps(
                "Content-Type {} is not allowed. Only application/json is allowed".format(
                    request.headers.environ['CONTENT_TYPE'])
            ), 415
        else:
            form = json.loads(request.data)
            error_msg = validate_login_form(form)
            if error_msg:
                return json.dumps("Invalid credentials specified: {}".format(error_msg)), 401
            token = get_or_create_token(form.get('email'))
            return json.dumps(token), 200


@router.route('/logout/', methods=['GET'])
def logout():
    """ Logout """
    if is_browser_request() and session.get('user'):
        del session['user']
        return redirect('/')
    return json.dumps('Logout is not available via API'), 400


@router.route('/register/', methods=['GET', 'POST'])
def register():
    """ User registration """
    if is_browser_request():
        if request.method == 'POST':
            form = request.form

            error_msg = validate_registration_form(form)

            if error_msg:
                return render_template(
                    'register.html', error=error_msg, email=form.get('email'),
                    password=form.get('password')
                ), requests.codes.bad_request

            email = str(form.get('email'))
            password = str(form.get('password'))
            user = Model(table='users')
            hashed_password = encrypt(password)
            user.create(row={'email': email, 'password': hashed_password})
            return redirect('/home'), requests.codes.found
        else:
            return render_template('register.html')
    else:
        if request.method != 'POST':
            return json.dumps("GET method is not allowed for this endpoint"), 405
        elif request.headers.environ['CONTENT_TYPE'] != 'application/json':
            return json.dumps(
                "Content-Type {} is not allowed. Only application/json is allowed".format(
                    request.headers.environ['CONTENT_TYPE'])
            ), 415
        else:
            form = json.loads(request.data)
            error_msg = validate_registration_form(form)
            if error_msg:
                return json.dumps("Invalid data specified: {}".format(error_msg)), 401
            email = str(form.get('email'))
            password = str(form.get('password'))
            user = Model(table='users')
            hashed_password = encrypt(password)
            user.create(row={'email': email, 'password': hashed_password})

            return json.dumps("User was successfully registered."), 200


@router.route('/alerts/', methods=['GET'])
@login_required
def alerts():
    """
    Monitoring stats route
    Use 'curl -O /static/alerts/video.mp4' to get video files
    """
    alert = Model(table='alerts')
    alerts = alert.read_all()
    resp = dict()
    resp['total'] = len(alerts)

    if request.args.get("detailed") == 'false':
        current_date = datetime.datetime.now()
        alerts_by_day = OrderedDict()
        for i in range(4, -1, -1):
            alerts_by_day[(current_date - datetime.timedelta(days=i)).strftime('%x')] = 0
        for al in alerts:
            alerts_by_day[al[2].split()[0]] += 1
        return json.dumps(alerts_by_day)

    else:
        resp['by_day'] = [
            list(group) for k, group in itertools.groupby(
                alerts, lambda d: datetime.datetime.strptime(d[2].split(' ')[0], '%x')
            )]
        resp['by_webcam'] = [
            list(group) for k, group in itertools.groupby(
                alerts, lambda d: d[1])
        ]

        if is_browser_request():
            return render_template('alerts.html', alerts=resp)
        return json.dumps(resp), 200


@router.route('/static/alerts/<file_name>')
def static_data(file_name):
    return send_from_directory('./static/alerts/', file_name)


@router.route('/static/docs/<file_name>')
def docs(file_name):
    return send_from_directory('./static/docs/', file_name)


@router.route('/help/')
@login_required
def help():
    """ FAQ page """
    if is_browser_request():
        return render_template('help.html')
    return json.dumps('Help page. Visit /help/ page in your browser to see full content.')


@router.route('/documentation/')
@login_required
def documentation():
    """ User guide and API doc """
    if is_browser_request():
        return render_template('documentation.html')
    return json.dumps({'url': ['/static/docs/api_guide.pdf', '/static/docs/user_guide.pdf']})
