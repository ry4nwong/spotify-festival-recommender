from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.db_init import Base
from app.models.associations import festival_tags, artist_tags

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
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