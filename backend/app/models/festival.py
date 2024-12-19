from app.models import db

class Festival(db.Model):
    __tablename__ = 'festivals'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(255), nullable=False)
    cancelled = db.Column(db.Boolean, default=False)
    artists = db.relationship(
        'Artist',
        secondary='festival_artists',
        backref=db.backref('festivals', lazy='dynamic')
    )
    tags = db.relationship(
        'Tag',
        secondary='festival_tags',
        backref=db.backref('festivals', lazy='dynamic')
    )