from sqlalchemy import Table, Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.db_init import Base

stage_festival_artists = Table(
    "stage_festival_artists",
    Base.metadata,
    Column("stage_festival_id", String(255), ForeignKey("stage_festivals.name", ondelete="CASCADE"), primary_key=True),
    Column("stage_artist_id", String(255), ForeignKey("stage_artists.name", ondelete="CASCADE"), primary_key=True)
)

stage_artist_tags = Table(
    "stage_artist_tags",
    Base.metadata,
    Column("stage_artist_id", String(255), ForeignKey("stage_artists.name", ondelete="CASCADE"), primary_key=True),
    Column("stage_tag_id", String(255), ForeignKey("stage_tags.name", ondelete="CASCADE"), primary_key=True)
)

stage_festival_tags = Table(
    "stage_festival_tags",
    Base.metadata,
    Column("stage_festival_id", String(255), ForeignKey("stage_festivals.name", ondelete="CASCADE"), primary_key=True),
    Column("stage_tag_id", String(255), ForeignKey("stage_tags.name", ondelete="CASCADE"), primary_key=True)
)