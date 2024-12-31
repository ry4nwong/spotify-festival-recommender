from shared.db_models import db

# Many-to-many relationship between artists and festivals
festival_artists = db.Table(
    'festival_artists',
    db.Column('festival_id', db.Integer, db.ForeignKey('festivals.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), primary_key=True)
)

# Many-to-many relationship between artists and tags
artist_tags = db.Table(
    'artist_tags',
    db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

# Many-to-many relationship between festivals and tags
festival_tags = db.Table(
    'festival_tags',
    db.Column('festival_id', db.Integer, db.ForeignKey('festivals.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)