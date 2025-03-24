from sqlalchemy import Table, Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.db_init import Base

festival_artists = Table(
    "festival_artists",
    Base.metadata,
    Column("festival_id", String(255), ForeignKey("festivals.name", ondelete="CASCADE"), primary_key=True),
    Column("artist_id", String(255), ForeignKey("artists.name", ondelete="CASCADE"), primary_key=True)
)

artist_tags = Table(
    "artist_tags",
    Base.metadata,
    Column("artist_id", String(255), ForeignKey("artists.name", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(255), ForeignKey("tags.name", ondelete="CASCADE"), primary_key=True)
)

festival_tags = Table(
    "festival_tags",
    Base.metadata,
    Column("festival_id", String(255), ForeignKey("festivals.name", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(255), ForeignKey("tags.name", ondelete="CASCADE"), primary_key=True)
)