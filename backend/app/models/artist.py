import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Text
from sqlalchemy.orm import relationship
from app.database.db_init import Base
from app.models.associations import artist_tags, festival_artists

class Artist(Base):
    __tablename__ = "artists"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    name = Column(Text, primary_key=True, nullable=False)
    festivals = relationship(
        "Festival",
        secondary=festival_artists,
        back_populates="artists",
        lazy="selectin"
    )
    genres = relationship(
        "Tag",
        secondary=artist_tags,
        back_populates="artists",
        lazy="selectin"
    )