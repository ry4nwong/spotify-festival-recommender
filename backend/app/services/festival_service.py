from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy.future import select
from sqlalchemy.sql import text
from datetime import date, datetime
from app.database.db_init import AsyncSessionLocal
from app.models.festival import Festival
from app.models.artist import Artist
from app.models.tag import Tag
from app.services.artist_service import save_artist_genre, create_or_get_artist, get_artists
from app.services.tag_service import create_or_get_tag, get_tags
from app.database.db_init import AsyncSessionLocal
import re

async def save_festival(festival_entry: dict):
    async with AsyncSessionLocal() as db:
        try:
            print(f"✅ Attempting to save festival: {festival_entry['name']}")
            festival, artists_added = await check_festival(festival_entry['name'], db)
            
            # Add new festival if does not exist
            if festival is None:
                print(f"✅ Creating new festival: {festival_entry['name']}")
                festival = Festival(
                    name=festival_entry['name'],
                    location=festival_entry['location'],
                    cancelled=festival_entry['cancelled'],
                    start_date=festival_entry['start_date'],
                    end_date=festival_entry['end_date']
                )

                # for tag in festival_entry['tags']:
                #     new_tag = await create_or_get_tag(tag, db)
                #     # Create Link
                #     festival.tags.append(new_tag)
                all_tags = await get_tags(festival_entry['tags'], db)
                

            # # Check if artists updated
            # if not artists_added and festival_entry['artists']:
            #     for artist in festival_entry['artists']:
            #         # accounts for b2b appearances (ex. Slander B2B Dimension)
            #         for each_artist in artist.split(' B2B '):
            #             new_artist, exists = await create_or_get_artist(each_artist, db)
            #             if not exists:
            #                 new_artists.append(new_artist.name)
            #             # Create link, automatically inputted into intermediate table
            #             if new_artist not in festival.artists:
            #                 festival.artists.append(new_artist)
                
            #     await save_artist_genre(new_artists, db)

            if (not artists_added) and festival_entry['artists']:
                all_artists = await get_artists(festival_entry['artists'], db)
                festival.artists.extend(all_artists)

            print(f"✅ Attempring to add festival: {festival_entry['name']}")
            db.add(festival)
            await db.commit()
            print(f"✅ Festival saved successfully: {festival_entry['name']}")
        except Exception as e:
            await db.rollback()
            print(f"❌ Error during save: {e}")
    
# Function to remove all past festivals
async def cleanup_past_festivals():
    async with AsyncSessionLocal() as db:
        try:
            today = date.today()
            result = await db.execute(select(Festival).filter(Festival.end_date < today))
            past_festivals = result.scalars().all()

            for festival in past_festivals:
                festival.artists.clear()
                festival.tags.clear()
                print("deleting festival " + festival.name)
                await db.delete(festival)

            await db.commit()

        except Exception as e:
            await db.rollback()
            print(f"An error occurred during cleanup: {e}")

# Helper function to parse start and end dates
def parse_festival_date(date_str):
    if date_str.strip().upper() == "CANCELLED":
        return None, None
    
    date_str = date_str.title()
    year = int(date_str.split(",")[1].strip())
    date_str = date_str.split(",")[0]

    if "-" not in date_str:
        start_date = datetime.strptime(f"{date_str} {year}", "%B %d %Y")
        return start_date, start_date
    
    date_str = date_str.replace("- ", "-").replace(" -", "-")

    if " " not in date_str.split("-")[1]:
        month, days = date_str.split()
        start_day, end_day = days.split("-")
        start_date = datetime.strptime(f"{month} {start_day} {year}", "%B %d %Y")
        end_date = datetime.strptime(f"{month} {end_day} {year}", "%B %d %Y")
        return start_date, end_date
    
    start_part, end_part = date_str.split("-")
    start_month, start_day = start_part.split(" ")
    end_month, end_day = end_part.split(" ")
    start_date = datetime.strptime(f"{start_month} {start_day} {year}", "%B %d %Y")
    end_date = datetime.strptime(f"{end_month} {end_day} {year}", "%B %d %Y")
    return start_date, end_date

# Returns festival if exists AND if artists already added
# returns festival (object), artists_added (boolean)
# def check_festival(festival_name):
#     festival = Festival.query.filter_by(name=festival_name).first()
#     artists_added = bool(festival.artists) if festival is not None else False

#     return festival, artists_added

async def check_festival(festival_name: str, db: AsyncSession):
    result = await db.execute(select(Festival).filter_by(name=festival_name))
    festival = result.scalars().first()
    artists_added = bool(festival.artists) if festival else False

    return festival, artists_added