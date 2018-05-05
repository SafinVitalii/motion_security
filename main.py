from flask import Flask
from processors.monitor import Monitor
from app.ui import home_page

app = Flask(__name__)

if __name__ == '__main__':
    app.register_blueprint(home_page)
    app.run(host='192.168.0.107')
    # monitor = Monitor(webcam_id=0)
    # monitor.capture_video_and_motion()
