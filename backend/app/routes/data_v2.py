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
from app.models.embedding import Embedding
from app.services.festival_service import save_festival, cleanup_past_festivals, parse_festival_date
from app.llm.sentence_transformer import generate_embedding, chunk_text
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

    tasks = [asyncio.create_task(scrape_festival_details(festival)) for festival in all_festivals]
    await asyncio.gather(*tasks)

    # TODO: deduplicate entries

    for festival in all_festivals:
        await save_temp_festival(festival, db)

    result = await db.execute(select(StageArtist))
    artists = result.scalars().all()

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

    # join stage tables with main tables
    await merge_stage_tables(db)

    # generate embeddings and put into table
    await generate_embeddings(all_festivals, db)

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
        end_date=festival.end_date
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

async def generate_embeddings(festivals: list, db):
    """Generates embeddings for a list of festivals."""
    all_chunks = []
    chunk_metadata = []

    for festival in festivals:
        artist_list = ", ".join(festival.artists) if festival.artists else "various artists"
        tag_list = ", ".join(festival.tags)

        chunks = chunk_text(
            f"{festival.name} is a festival in {festival.location} on {festival.date}. "
            f"Featured artists include: {artist_list}. "
            f"Featured tags include: {tag_list}."
        )
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            chunk_metadata.append((festival, i, chunk))

    embeddings = await generate_embedding(all_chunks)

    for (festival, index, text), embedding in zip(chunk_metadata, embeddings):
        new_embedding = Embedding(name=festival.name, chunk_index=index, text=text, embedding=embedding)
        await db.merge(new_embedding)

    await db.commit()

async def merge_stage_tables(db):
    """Merges the stage tables with the main tables."""

    await db.execute(text("""
        INSERT INTO festivals (id, name, location, cancelled, start_date, end_date)
        SELECT id, name, location, cancelled, start_date, end_date
        FROM stage_festivals
        ON CONFLICT (name) DO NOTHING;
    """))

    await db.execute(text("""
        INSERT INTO artists (id, name)
        SELECT id, name
        FROM stage_artists
        ON CONFLICT (name) DO NOTHING;
    """))

    await db.execute(text("""
        INSERT INTO tags (id, name)
        SELECT id, name
        FROM stage_tags
        ON CONFLICT (name) DO NOTHING;
    """))

    await db.execute(text("""
        INSERT INTO festival_artists (festival_id, artist_id)
        SELECT fa.stage_festival_id, fa.stage_artist_id
        FROM stage_festival_artists fa
        JOIN stage_festivals fs ON fa.stage_festival_id = fs.name
        JOIN stage_artists ast ON fa.stage_artist_id = ast.name
        ON CONFLICT (festival_id, artist_id) DO NOTHING;
    """))

    await db.execute(text("""
        INSERT INTO festival_tags (festival_id, tag_id)
        SELECT fa.stage_festival_id, fa.stage_tag_id
        FROM stage_festival_tags fa
        JOIN stage_festivals fs ON fa.stage_festival_id = fs.name
        JOIN stage_tags ast ON fa.stage_tag_id = ast.name
        ON CONFLICT (festival_id, tag_id) DO NOTHING;
    """))

    await db.execute(text("""
        INSERT INTO artist_tags (artist_id, tag_id)
        SELECT fa.stage_artist_id, fa.stage_tag_id
        FROM stage_artist_tags fa
        JOIN stage_artists fs ON fa.stage_artist_id = fs.name
        JOIN stage_tags ast ON fa.stage_tag_id = ast.name
        ON CONFLICT (artist_id, tag_id) DO NOTHING;
    """))

    await db.execute(text("DELETE FROM stage_festivals"))
    await db.execute(text("DELETE FROM stage_artists"))
    await db.execute(text("DELETE FROM stage_tags"))
    await db.execute(text("DELETE FROM stage_festival_artists"))
    await db.execute(text("DELETE FROM stage_festival_tags"))
    await db.execute(text("DELETE FROM stage_artist_tags"))

    await db.commit()


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