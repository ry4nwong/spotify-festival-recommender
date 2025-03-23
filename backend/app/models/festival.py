import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database.db_init import Base
from app.models.associations import festival_artists, festival_tags

class Festival(Base):
    __tablename__ = "festivals"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    name = Column(String(255), primary_key=True, nullable=False)
    location = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    cancelled = Column(Boolean, default=False)
    embedding_chunks = relationship("Embedding", back_populates="festival", uselist=False, cascade="all, delete-orphan")
    artists = relationship(
        "Artist",
        secondary=festival_artists,
        back_populates="festivals",
        lazy="selectin"
    )
    tags = relationship(
        "Tag",
        secondary=festival_tags,
        back_populates="festivals",
        lazy="selectin"
    )