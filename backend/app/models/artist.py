# Artist: id, name (string), genre (list for now)
from app.models import db

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255), nullable = False)
    genre = db.Column(db.String(255))