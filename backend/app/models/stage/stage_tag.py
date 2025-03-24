import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.db_init import Base
from app.models.stage.stage_associations import stage_festival_tags, stage_artist_tags

class StageTag(Base):
    __tablename__ = "stage_tags"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    name = Column(String(255), primary_key=True, nullable=False)
    stage_festivals = relationship(
        "StageFestival",
        secondary=stage_festival_tags,
        back_populates="stage_tags",
        lazy="selectin"
    )
    stage_artists = relationship(
        "StageArtist",
        secondary=stage_artist_tags,
        back_populates="stage_genres",
        lazy="selectin"
    )