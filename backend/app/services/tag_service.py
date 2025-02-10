from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy.future import select
from app.models.tag import Tag
from app.database.db_init import AsyncSessionLocal

# Helper function to get or create tag in database
async def create_or_get_tag(tag_name: str, db: AsyncSession):
    result = await db.execute(select(Tag).filter_by(name=tag_name))
    existing_tag = result.scalars().first()

    if not existing_tag:
        new_tag = Tag(name=tag_name)
        db.add(new_tag)
        # await db.commit()
        # await db.refresh(new_tag)
        return new_tag
    else:
        return existing_tag
    
# Gets a list of tags and creates new ones if not existing
# Returns list of tags to be attached to festival/artist
async def get_tags(tag_list: list, db: AsyncSession) -> list:
    existing = await db.execute(select(Tag).where(Tag.name.in_(tag_list)))
    existing_tags = existing.scalars().all()

    missing_tags = set(tag_list) - {tag.name for tag in existing_tags}

    new_tags = []
    for tag in missing_tags:
        new_tag = Tag(name=tag)
        new_tags.append(new_tag)
    
    db.add_all(new_tags)
    await db.commit()
    return existing_tags + new_tags