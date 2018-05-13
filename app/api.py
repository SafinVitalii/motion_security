import re
from email.utils import parseaddr

import requests
from flask import Blueprint, render_template, Response, request, session
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from app.auth import encrypt, verify_password, login_required
from app.info import available_devices
from models.model import Model
from processors.monitor import Monitor, d

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
    return render_template('home.html', devices=available_devices(), user=session['user'])


@router.route('/devices/<device_id>')
@login_required
def device(device_id):
    """ Camera home """
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

    camera_config = d[int(device_id)].get_config()
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


@router.route('/devices/<device_id>/content/')
@login_required
def content(device_id):
    """ Page for video frame """
    return render_template('content.html', video_url='/devices/{}/video/'.format(int(device_id)))


@router.route('/devices/<int:device_id>/video/')
@login_required
def video(device_id):
    """ Video streaming route. Put this in the src attribute of an img tag """
    monitor = Monitor(webcam_id=int(device_id), subscribers=[], streaming=True)
    return Response(monitor.stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@router.route('/login/', methods=['GET', 'POST'])
def login():
    """ Login page """
    if request.method == 'POST':
        form = request.form

        error_msg = None
        if not form.get('email') or not form.get('password'):
            error_msg = 'Both email and password are required!'

        email = form.get('email')
        password = str(form.get('password'))
        result = verify_password(email, password)

        if not result:
            error_msg = 'Error occured when logging in. Please verify your credentials.'

        if error_msg:
            return render_template(
                'login.html', error=error_msg, email=form.get('email'),
                password=form.get('password')
            ), requests.codes.bad_request

        return redirect('/home'), requests.codes.ok

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
        return redirect('/home')
    else:
        return render_template('register.html')


@router.route('/help/')
def help():
    """ FAQ page """
    return render_template('help.html')


@router.route('/documentation/')
@login_required
def documentation():
    """ User guide and API doc """
    return render_template('documentation.html')
