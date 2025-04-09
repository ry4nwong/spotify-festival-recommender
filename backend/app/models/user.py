import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database.db_init import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id = Column(String(255), primary_key=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    profile_picture = Column(String(255), nullable=True)
    token = relationship("AuthToken", back_populates="user", uselist=False)