from app.models import db

# Still needs artists (list), tags (list)
class Festival(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    artists = db.Column(db.String(255))
    location = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    tags = db.Column(db.String(255))
