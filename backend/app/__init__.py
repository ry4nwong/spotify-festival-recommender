from flask import Flask
from dotenv import load_dotenv
import os
from app.routes import api_blueprint, auth_blueprint, data_blueprint

# Initialize Flask app with blueprint (API route structure)
def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')

    app.config['SPOTIFY_CLIENT_ID'] = os.getenv('CLIENT_ID')
    app.config['SPOTIFY_CLIENT_SECRET'] = os.getenv('CLIENT_SECRET')
    app.config['SPOTIFY_REDIRECT_URI'] = os.getenv('REDIRECT_URI')

    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.register_blueprint(data_blueprint, url_prefix='/data')

    return app