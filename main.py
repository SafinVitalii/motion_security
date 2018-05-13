from flask import Flask
from flask_session import Session

from app.api import router
from db.database import Database

app = Flask(__name__)
s = Session()

if __name__ == '__main__':
    Database().setup()
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    s.init_app(app)

    app.register_blueprint(router)
    app.run()
    # monitor = Monitor(webcam_id=0)
    # monitor.capture_video_and_motion()
