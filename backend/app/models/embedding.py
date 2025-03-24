import uuid
from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database.db_init import Base

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), ForeignKey("festivals.name", ondelete="CASCADE"))
    chunk_index = Column(Integer, nullable = False)
    text = Column(String, nullable=False)
    embedding = Column(Vector(768), nullable=False)
    festival = relationship("Festival", back_populates="embedding_chunks", uselist=False)
    
    