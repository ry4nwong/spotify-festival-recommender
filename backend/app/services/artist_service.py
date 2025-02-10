from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from sqlalchemy.future import select
from app.models.artist import Artist
from app.services.tag_service import create_or_get_tag, get_tags
from app.database.dependencies import get_db
import musicbrainzngs
import asyncio
import time

# Function to run web scraper on genre for each artist and persist in database
async def save_artist_genre(new_artists: list, db: AsyncSession):
    # Get genres for each new artist
    artist_genres = await all_artist_genre(new_artists)

    for artist_name, genre_list in artist_genres.items():
        # Fetch artist
        result = await db.execute(select(Artist).filter_by(name=artist_name))
        artist = result.scalars().first()

        if artist:
            for genre_string in genre_list:
                genre_tag = await create_or_get_tag(genre_string, db)
                if genre_tag not in artist.genres:
                    artist.genres.append(genre_tag)

    # await db.commit()

# Helper function to get or create artist in database
async def create_or_get_artist(artist_name: str, db: AsyncSession):
    result = await db.execute(select(Artist).filter_by(name=artist_name))
    existing_artist = result.scalars().first()

    if not existing_artist:
        new_artist = Artist(name=artist_name)
        db.add(new_artist)
        # await db.commit()
        # await db.refresh(new_artist)
        # Artist did not exist
        return new_artist, False
    else:
        # Artist exists
        return existing_artist, True
    

# Gets string list of artists
# Returns list of artist objects to be linked to festival
async def get_artists(artist_list: list, db: AsyncSession) -> list:
    existing = await db.execute(select(Artist).where(Artist.name.in_(artist_list)))
    existing_artists = existing.scalars().all()

    missing_artists = set(artist_list) - {artist.name for artist in existing_artists}

    new_artists = []
    for artist in missing_artists:
        new_artist = Artist(name=artist)
        # Gather all genres
        genres = await webscrape_artist_genre(artist, db)
        new_artist.genres.extend(genres)
        new_artists.append(new_artist)
        
    db.add_all(new_artists)
    return new_artists + existing_artists
        
    
# Finds artist genres based on name
async def webscrape_artist_genre(artist_name: str, db: AsyncSession):
    artist_name = artist_name.lower().replace(' ', '-').replace('&', 'and')

    musicbrainzngs.set_useragent("spotify_music_recommender project", version='1')
    
    artist_data = musicbrainzngs.search_artists(query=artist_name, limit=1)['artist-list']
    
    if not artist_data:
        return []

    genre_output = []
    if 'tag-list' in artist_data[0]:
        # Extract genres with upvotes only
        genre_output = [
            tag['name'] for tag in artist_data[0]['tag-list'] if int(tag['count']) >= 0
        ]

    genres = await get_tags(genre_output, db)
    return genres

# function that scrapes all artist genre info given list of artists
async def all_artist_genre(all_artists: list):
    artist_genre = {}

    for artist in all_artists:
        output = await webscrape_artist_genre(artist)
        artist_genre[artist] = output if artist not in artist_genre else artist_genre[artist] + output
        time.sleep(1)

    return artist_genre