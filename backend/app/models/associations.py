from sqlalchemy import Table, Column, Integer, ForeignKey
from app.database.db_init import Base

festival_artists = Table(
    "festival_artists",
    Base.metadata,
    Column("festival_id", Integer, ForeignKey("festivals.id", ondelete="CASCADE"), primary_key=True),
    Column("artist_id", Integer, ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True)
)

artist_tags = Table(
    "artist_tags",
    Base.metadata,
    Column("artist_id", Integer, ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

festival_tags = Table(
    "festival_tags",
    Base.metadata,
    Column("festival_id", Integer, ForeignKey("festivals.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)