from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database.db_init import Base
from app.models.associations import festival_artists, festival_tags

class Festival(Base):
    __tablename__ = "festivals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    cancelled = Column(Boolean, default=False)
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