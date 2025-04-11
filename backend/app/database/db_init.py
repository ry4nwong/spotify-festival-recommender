from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

async_engine: AsyncEngine = create_async_engine(
    os.getenv("DATABASE_URI"), 
    echo=True, 
    future=True, 
    pool_size=25, 
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

from app.models.stage.stage_festival import StageFestival
from app.models.stage.stage_associations import stage_festival_artists, stage_festival_tags, stage_artist_tags
from app.models.stage.stage_artist import StageArtist
from app.models.stage.stage_tag import StageTag

from app.models.artist import Artist
from app.models.festival import Festival
from app.models.tag import Tag
from app.models.embedding import Embedding
from app.models.associations import festival_artists, artist_tags, festival_tags

from app.models.user import User
from app.models.auth_token import AuthToken

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)