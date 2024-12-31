from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .festival import Festival
from .artist import Artist
from .tag import Tag
from .associations import festival_artists, festival_tags, artist_tags

print('Initializing database...')


