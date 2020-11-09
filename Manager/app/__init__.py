from flask import Flask


# Init Flask application object
app = Flask(__name__)
app.config.from_object('app.settings')


# Register all blueprints
from .controllers import home
app.register_blueprint(home.bp, url_prefix='/')


