import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.future import select
from app.database.dependencies import get_db
from app.models.stage.stage_festival import StageFestival
from app.models.stage.stage_artist import StageArtist
from app.models.stage.stage_tag import StageTag
from app.services.festival_service import save_festival, cleanup_past_festivals, parse_festival_date
from app.llm.sentence_transformer import generate_embedding
from bs4 import BeautifulSoup
import requests
import aiohttp
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor

data_router2 = APIRouter(prefix="/data2", tags=["Data"])

class TempFestival:
    def __init__(self, name, location, date, link):
        self.name = name
        self.date = date
        self.location = location
        self.link = link

async def new_webdriver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--blink-settings=imagesEnabled=false")

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver

@data_router2.get("/scrape-mfw")
async def webscrape_all_festivals(db: AsyncSession = Depends(get_db)):
    start_time = time.perf_counter()

    """Obtains all US and electronic music festivals from musicfestivalwizard."""
    all_festivals = []
    
    driver = await new_webdriver()
    festival_url = "https://www.musicfestivalwizard.com/all-festivals/?festival_guide=us-festivals&festivalgenre=electronic"
    driver.get(festival_url)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    elements = soup.find_all("div", class_="entry-title search-title")
    for element in elements:
        # [name, location, date]
        festival_info = element.get_text(separator='|', strip=True).split("|")
        # print(festival_info)
        a_tag = element.find("a")
        correct_date = lambda x: x.split('/')[0] if '/' in x else x
        if a_tag:
            page_link = a_tag["href"]
            all_festivals.append(TempFestival(festival_info[0], festival_info[1], correct_date(festival_info[2]), page_link))

    # TODO: Check if festival already exists in database

    tasks = [asyncio.create_task(scrape_festival_details(festival)) for festival in all_festivals[:5]]
    await asyncio.gather(*tasks)

    for festival in all_festivals[:5]:
        await save_temp_festival(festival, db)

    # await deduplicate_entries(db)

    result = await db.execute(select(StageArtist))
    artists = result.scalars().all()

    all_tags = []
    batch_size = 50
    for i in range(0, len(artists), batch_size):
        batch = artists[i : i + batch_size]
        artist_tasks = [gather_lastfm_tags(artist.name) for artist in batch]
        batch_results = await asyncio.gather(*artist_tasks)
        # all_tags.extend(batch_results)

        for artist, tags in zip(batch, batch_results):
            merged_tags = [await db.merge(StageTag(name=tag)) for tag in tags]
            for tag in merged_tags:
                if tag not in artist.stage_genres:
                    artist.stage_genres.append(tag)
            await db.merge(artist)

    await db.commit()

    end_time = time.perf_counter()
    return JSONResponse(content={"time": end_time - start_time})

    # gather artist tag information from last.fm
    
async def scrape_festival_details(festival):
    """Scrapes detailed information on a festival."""
    driver = await new_webdriver()
    driver.get(festival.link)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    artist_elements = soup.find_all("div", class_="lineupblock")
    artists = [element.get_text(separator='|', strip=True).split("|") for element in artist_elements]
    artists = artists[0] if artists else []
    # need to find way to split b2b and vs artists
    festival.artists = artists

    tag_elements = soup.find_all("span", class_="heading-breadcrumb")
    tags = [element.get_text(separator='|', strip=True).split("|") for element in tag_elements]
    if tags:
        tags = tags[0]
    festival.tags = tags

    start_date, end_date = parse_festival_date(festival.date)
    is_cancelled = start_date is None
    if is_cancelled:
        festival.artists = []
    festival.start_date = start_date
    festival.end_date = end_date
    festival.cancelled = is_cancelled

async def save_temp_festival(festival, db):
    """Saves a temporary festival object to the database."""
    new_festival = StageFestival(
        name=festival.name, 
        location=festival.location, 
        cancelled=festival.cancelled,
        start_date=festival.start_date, 
        end_date=festival.end_date,
        embedding=await generate_embedding(festival)
    )

    for artist in festival.artists:
        new_artist = await db.merge(StageArtist(name=artist))
        if new_artist not in new_festival.stage_artists:
            new_festival.stage_artists.append(new_artist)

    for tag in festival.tags:
        new_tag = await db.merge(StageTag(name=tag))
        if new_tag not in new_festival.stage_tags:
            new_festival.stage_tags.append(new_tag)

    await db.merge(new_festival)
    await db.commit()

async def deduplicate_entries(db):
    """Deduplicates entries in the database."""

    await deduplicate_artists(db)
    await deduplicate_tags(db)

    # check if festival already exists, update relationships
    await db.execute(text("""
        INSERT INTO festival_artists (festival_id, artist_id)
        SELECT f.id, sfa.stage_artist_id
        FROM stage_festival_artists sfa
        JOIN festivals f ON f.name = (SELECT name FROM stage_festivals WHERE id = sfa.stage_festival_id)
        ON CONFLICT (festival_id, artist_id) DO NOTHING;
    """))

    # delete tag relationships (no need to preserve)
    await db.execute(text("""
        DELETE FROM stage_festival_tags
        WHERE stage_festival_id IN (
            SELECT sf.id FROM stage_festivals sf
            JOIN festivals f ON sf.name = f.name
        );
    """))

    # delete duplicate festival entries
    await db.execute(text("""
        DELETE FROM stage_festivals
        WHERE id IN (
            SELECT sf.id FROM stage_festivals sf
            JOIN festivals f ON sf.name = f.name
        );
    """))

    # update artist relationships to point to permanent artist
    await db.execute(text("""
        UPDATE stage_festival_artists sfa
        SET stage_artist_id = a.id
        FROM artists a
        WHERE sfa.stage_artist_id IN (
            SELECT sa.id FROM stage_artists sa
            WHERE sa.name = a.name
        );
    """))

    # delete already existing artists
    await db.execute(text("""
        DELETE FROM stage_artists 
        WHERE name IN (SELECT name FROM artists);
    """))

    await db.commit()

async def deduplicate_tags(db):
    """Deduplicates stage_tags while preserving festival-tag links."""

    # Step 1: Create a mapping from duplicate tags to a single correct tag_id
    await db.execute(text("""
        CREATE TEMP TABLE tag_mapping AS
        SELECT id AS old_id, 
               FIRST_VALUE(id) OVER (PARTITION BY name ORDER BY id) AS new_id
        FROM stage_tags;
    """))

    # Step 2: Update stage_festival_tags to use the correct tag_id
    await db.execute(text("""
        UPDATE stage_festival_tags sft
        SET stage_tag_id = tm.new_id
        FROM tag_mapping tm
        WHERE sft.stage_tag_id = tm.old_id;
    """))

    # Step 3: Delete duplicate tags from stage_tags
    # await db.execute(text("""
    #     DELETE FROM stage_tags 
    #     WHERE id IN (SELECT old_id FROM tag_mapping WHERE old_id != new_id);
    # """))

    # Step 4: Drop temporary mapping table
    await db.execute(text("DROP TABLE tag_mapping;"))

    await db.commit()

async def deduplicate_artists(db):
    """Deduplicates stage_artists while preserving festival-artist links."""

    # Step 1: Create a mapping from duplicate tags to a single correct tag_id
    await db.execute(text("""
        CREATE TEMP TABLE artist_mapping AS
        SELECT id AS old_id, 
               FIRST_VALUE(id) OVER (PARTITION BY name ORDER BY id) AS new_id
        FROM stage_artists;
    """))

    # Step 2: Update stage_festival_artists to use the correct tag_id
    await db.execute(text("""
        UPDATE stage_festival_artists sfa
        SET stage_artist_id = am.new_id
        FROM artist_mapping am
        WHERE sfa.stage_artist_id = am.old_id;
    """))

    # Step 3: Delete duplicate tags from stage_tags
    await db.execute(text("""
        DELETE FROM stage_artists
        WHERE id IN (SELECT old_id FROM artist_mapping WHERE old_id != new_id);
    """))

    # Step 4: Drop temporary mapping table
    await db.execute(text("DROP TABLE artist_mapping;"))

    await db.commit()

lastfm_rate_limit = asyncio.Semaphore(10)

async def gather_lastfm_tags(artist: str):
    url = f"https://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist={urllib.parse.quote(artist)}&api_key=987e94fc27d8d427dc7f119842b9101e&format=json"

    async with lastfm_rate_limit:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        
        await asyncio.sleep(0.5)
    
    tags_list = data.get("toptags", {}).get("tag", [])
    sorted_tags = sorted(tags_list, key=lambda tag: tag["count"], reverse=True)
    top_tags = [tag["name"].title() for tag in sorted_tags[:5]]

    return top_tags

async def generate_embedding(festival):
    """Formats a festival object for embedding."""
    artist_list = ", ".join(festival.artists) if festival.artists else "various artists"
    tag_list = ", ".join(festival.tags)

    return await generate_embedding(
        f"{festival.name} is a {tag_list} in {festival.location} on {festival.date}. "
        f"Featured artists include: {artist_list}. "
        f"Featured tags include: {tag_list}."
    )

@data_router2.get("/test-lastfm")
async def test_lastfm(name: str):
    """Tests the last.fm API."""
    url2 = f"https://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist={urllib.parse.quote(name)}&api_key=987e94fc27d8d427dc7f119842b9101e&format=json"
    url = "https://ws.audioscrobbler.com/2.0/?method=album.gettoptags&artist=radiohead&album=the%20bends&api_key=987e94fc27d8d427dc7f119842b9101e&format=json"

    response = requests.get(url2)
    data = response.json()
    tags_list = data.get("toptags", {}).get("tag", [])
    sorted_tags = sorted(tags_list, key=lambda tag: tag["count"], reverse=True)
    top_tags = [tag["name"] for tag in sorted_tags[:5]]

    return JSONResponse(content={"tags": top_tags})