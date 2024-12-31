from flask import Flask
from dotenv import load_dotenv
import os
from shared.db_models import db
from llm.routes import llm_blueprint

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

    # Register routes
    app.register_blueprint(llm_blueprint, url_prefix='/llm')

    return app