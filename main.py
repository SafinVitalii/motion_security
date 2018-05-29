from flask import Flask
from flask_session import Session

from app.api import router
from db.database import Database
from processors.monitor import MonitorContainer

app = Flask(__name__)
container = MonitorContainer()
s = Session()

if __name__ == '__main__':
    Database().setup()
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    s.init_app(app)

    app.register_blueprint(router)
    app.run(host='192.168.0.103')
