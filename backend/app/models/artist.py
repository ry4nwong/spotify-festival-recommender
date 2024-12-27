# Artist: id, name (string), genre (list for now)
from app.models import db

class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    genres = db.relationship(
        'Tag',
        secondary='artist_tags',
        backref=db.backref('artists', lazy='dynamic')
    )