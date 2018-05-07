from flask import Flask
from app.ui import router

app = Flask(__name__)

if __name__ == '__main__':
    app.register_blueprint(router)
    app.run()
    # monitor = Monitor(webcam_id=0)
    # monitor.capture_video_and_motion()
