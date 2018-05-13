from flask import Flask
from flask_session import Session

from app.api import router
from db.database import Database
from processors.monitor import setup_monitors

app = Flask(__name__)
s = Session()

if __name__ == '__main__':
    Database().setup()
    setup_monitors()
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    s.init_app(app)

    app.register_blueprint(router)
    app.run()
