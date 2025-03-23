import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database.db_init import Base
from app.models.stage.stage_associations import stage_festival_artists, stage_festival_tags

class StageFestival(Base):
    __tablename__ = "stage_festivals"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    name = Column(String(255), primary_key=True, nullable=False)
    location = Column(String(255), nullable=False)
    cancelled = Column(Boolean, default=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    stage_artists = relationship(
        "StageArtist",
        secondary=stage_festival_artists,
        back_populates="stage_festivals",
        lazy="selectin"
    )
    stage_tags = relationship(
        "StageTag",
        secondary=stage_festival_tags,
        back_populates="stage_festivals",
        lazy="selectin"
    )