from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.stage.stage_artist import StageArtist
from app.models.stage.stage_tag import StageTag
import asyncio
import aiohttp
import urllib.parse
import os


async def batch_search_artists(batch_size: int, db: AsyncSession):
    """Concurrently searches batch_size artists until none left, inserts into database for processing."""
    result = await db.execute(select(StageArtist))
    artists = result.scalars().all()

    for i in range(0, len(artists), batch_size):
        batch = artists[i : i + batch_size]
        artist_tasks = [gather_lastfm_tags(artist.name) for artist in batch]
        batch_results = await asyncio.gather(*artist_tasks)

        for artist, tags in zip(batch, batch_results):
            merged_tags = [await db.merge(StageTag(name=tag)) for tag in tags]
            for tag in merged_tags:
                if tag not in artist.stage_genres:
                    artist.stage_genres.append(tag)
            await db.merge(artist)

    await db.commit()

lastfm_rate_limit = asyncio.Semaphore(10)

async def gather_lastfm_tags(artist: str):
    """Gathers an artist's genre tags from last.fm."""
    url = f"https://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist={urllib.parse.quote(artist)}&api_key={os.getenv('LASTFM_API_KEY')}&format=json"

    async with lastfm_rate_limit:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        
        await asyncio.sleep(0.5)
    
    tags_list = data.get("toptags", {}).get("tag", [])
    sorted_tags = sorted(tags_list, key=lambda tag: tag["count"], reverse=True)
    top_tags = [tag["name"].title() for tag in sorted_tags[:5]]

    return top_tags