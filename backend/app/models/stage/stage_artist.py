import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.db_init import Base
from app.models.stage.stage_associations import stage_artist_tags, stage_festival_artists

class StageArtist(Base):
    __tablename__ = "stage_artists"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    name = Column(String(255), primary_key=True, nullable=False)
    stage_festivals = relationship(
        "StageFestival",
        secondary=stage_festival_artists,
        back_populates="stage_artists",
        lazy="selectin"
    )
    stage_genres = relationship(
        "StageTag",
        secondary=stage_artist_tags,
        back_populates="stage_artists",
        lazy="selectin"
    )