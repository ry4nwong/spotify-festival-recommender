import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db_init import Base

class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id"), primary_key=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user = relationship("User", back_populates="token", uselist=False)
