import itertools

import datetime
import json

import requests
from flask import Blueprint, render_template, Response, request, session, send_from_directory
from werkzeug.exceptions import abort
from werkzeug.utils import redirect
from collections import OrderedDict
from app.auth import encrypt, login_required
from app.info import available_devices
from models.model import Model
from processors.monitor import Monitor, STATUS_LIVE, STATUS_PROVISIONING, STATUS_AVAILABLE
from validators.validators import validate_registration_form, validate_login_form

router = Blueprint('router', __name__, template_folder='templates')


@router.route('/')
@router.route('/index/')
def index():
    """ Index page """
    return render_template('index.html')


@router.route('/home/')
@login_required
def home():
    """ Dashboard """
    from main import container
    return render_template('home.html', devices=container.available_devices(), user=session['user'])

@router.route('/navigation/')
@login_required
def navigation():
    """ Navigation """
    from main import container
    return render_template('navigation.html', user=session['user'])

@router.route('/devices/')
@login_required
def devices_redirect():
    """ Redirect to home """
    return redirect('/home'), requests.codes.found


@router.route('/devices/<device_id>/')
@login_required
def device(device_id):
    """ Camera home """
    from main import container
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

    camera_config = container.d[int(device_id)].get_config()
    # Sample config:
    # camera_config = {
    #   'CV_CAP_PROP_POS_MSEC': "Current position of the video file in milliseconds",
    #  'CV_CAP_PROP_POS_FRAMES': " 0-based index of the frame to be decoded/captured next.",
    # 'CV_CAP_PROP_POS_AVI_RATIO': " Relative position of the video file",
    # 'CV_CAP_PROP_FRAME_WIDTH': " Width of the frames in the video stream.",
    #    'CV_CAP_PROP_FRAME_HEIGHT': " Height of the frames in the video stream.",
    #   'CV_CAP_PROP_FPS': " Frame rate.",
    #  'CV_CAP_PROP_FOURCC': " 4-character code of codec.",
    # 'CV_CAP_PROP_FRAME_COUNT': " Number of frames in the video file.",
    # 'CV_CAP_PROP_FORMAT': " Format of the Mat objects returned by retrieve() .",
    #    'CV_CAP_PROP_MODE': " Backend-specific value indicating the current capture mode.",
    #   'CV_CAP_PROP_BRIGHTNESS': " Brightness of the image (only for cameras).",
    #  'CV_CAP_PROP_CONTRAST': " Contrast of the image (only for cameras).",
    # 'CV_CAP_PROP_SATURATION': " Saturation of the image (only for cameras).",
    # 'CV_CAP_PROP_HUE': " Hue of the image (only for cameras).",
    #   'CV_CAP_PROP_GAIN': " Gain of the image (only for cameras).",
    #   'CV_CAP_PROP_EXPOSURE': " Exposure (only for cameras).",
    #  'CV_CAP_PROP_CONVERT_RGB': " Boolean flags indicating whether images should be converted to RGB.",
    # 'CV_CAP_PROP_WHITE_BALANCE': " Currently unsupported",
    # 'CV_CAP_PROP_RECTIFICATION': " Rectification flag for stereo cameras"
    # }
    return render_template('device.html', device_id=device_id,
                           content_url='/devices/{}/content/'.format(int(device_id)),
                           camera_config=camera_config)


@router.route('/devices/<int:device_id>/content/')
@login_required
def content(device_id):
    """ Page for video frame """
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
        container.d[device_id].start()
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
    return '', 403


@router.route('/devices/<int:device_id>/configuration/', methods=['GET', 'POST'])
@login_required
def configuration(device_id):
    """ Page for monitoring configurations """

    if request.method == 'POST':
        from main import container

        form = request.form
        error_msg = None
        subscribers = form.get('subscribers').split(',')
        duration = int(form.get('duration'))
        fps = float(form.get('fps'))

        # verify for errors and set error_msg

        if error_msg:
            return render_template(
                'configuration.html', error=error_msg, subscribers=subscribers,
                duration=duration, fps=fps
            ), requests.codes.bad_request

        container.d[device_id].subscribers = subscribers
        container.d[device_id].default_buffer_duration = duration
        container.d[device_id].camera_fps = fps

        monitor = container.d[device_id]
        return render_template(
            'configuration.html', subscribers=','.join(monitor.subscribers),
            duration=monitor.default_buffer_duration, fps=monitor.camera_fps,
            device_id=device_id, success="Configurations were changed successfully."
        )

    else:
        from main import container
        monitor = container.d[device_id]
        return render_template(
            'configuration.html', subscribers=','.join(monitor.subscribers),
            duration=monitor.default_buffer_duration, fps=monitor.camera_fps,
            device_id=device_id
        )


@router.route('/login/', methods=['GET', 'POST'])
def login():
    """ Login page """
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


@router.route('/logout/', methods=['GET'])
def logout():
    """ Logout """
    del session['user']
    return redirect('/')


@router.route('/register/', methods=['GET', 'POST'])
def register():
    """ User registration """
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


@router.route('/alerts/', methods=['GET'])
def alerts():
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

        return render_template('alerts.html', alerts=resp)


@router.route('/static/alerts/<file_name>')
def static_data(file_name):
    return send_from_directory('./static/alerts/', file_name)


@router.route('/help/')
@login_required
def help():
    """ FAQ page """
    return render_template('help.html')


@router.route('/documentation/')
@login_required
def documentation():
    """ User guide and API doc """
    return render_template('documentation.html')
