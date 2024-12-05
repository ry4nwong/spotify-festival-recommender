from app import db

# Associates many-to-many relationship btwn artists and festivals
festival_artists = db.Table(
    'festival_artists',
    db.Column('festival_id', db.Integer, db.ForeignKey('festivals.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), primary_key=True)
)