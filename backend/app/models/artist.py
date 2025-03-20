import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.db_init import Base
from app.models.associations import artist_tags, festival_artists

class Artist(Base):
    __tablename__ = "artists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
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