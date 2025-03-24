import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.db_init import Base
from app.models.associations import festival_tags, artist_tags

class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    name = Column(String(255), primary_key=True, nullable=False)
    festivals = relationship(
        "Festival",
        secondary=festival_tags,
        back_populates="tags",
        lazy="selectin"
    )
    artists = relationship(
        "Artist",
        secondary=artist_tags,
        back_populates="genres",
        lazy="selectin"
    )