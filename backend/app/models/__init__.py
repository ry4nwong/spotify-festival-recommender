from flask_sqlalchemy import SQLAlchemy
import app

db = SQLAlchemy()

from .festival import Festival
from .artist import Artist

print('initializing database...')

# db.create_all()


