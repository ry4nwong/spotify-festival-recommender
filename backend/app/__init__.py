from flask import Flask
from dotenv import load_dotenv
import os
from app.models import db
from app.routes import api_blueprint, auth_blueprint, data_blueprint

# Initialize Flask app with blueprint (API route structure)
def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')

    # Database connection
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Spotify Auth
    app.config['SPOTIFY_CLIENT_ID'] = os.getenv('CLIENT_ID')
    app.config['SPOTIFY_CLIENT_SECRET'] = os.getenv('CLIENT_SECRET')
    app.config['SPOTIFY_REDIRECT_URI'] = os.getenv('REDIRECT_URI')

    # Register routes
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.register_blueprint(data_blueprint, url_prefix='/data')

    return app