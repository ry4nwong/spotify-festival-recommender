from app.models.stage.stage_artist import StageArtist
from app.models.stage.stage_festival import StageFestival
from app.models.stage.stage_tag import StageTag
from app.models.festival import Festival
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.services import utils, artist_service, llm_service
import asyncio
import re

class TempFestival:
    """Class to represent a festival object before inserting into the database."""
    def __init__(self, name: str, location: str, date: datetime, link: str):
        self.name = name
        self.date = date
        self.location = location
        self.link = link

async def webscrape_all_festivals(db: AsyncSession):
    """Scrapes all festival information from musicfestivalwizard. Generates embeddings and stores all information."""
    all_festivals = []
    
    festival_url = "https://www.musicfestivalwizard.com/all-festivals/?festival_guide=us-festivals&festivalgenre=electronic"
    soup = await utils.get_html(festival_url)

    elements = soup.find_all("div", class_="entry-title search-title")
    for element in elements:
        # [name, location, date]
        festival_info = element.get_text(separator='|', strip=True).split("|")
        a_tag = element.find("a")
        correct_date = lambda x: x.split('/')[0] if '/' in x else x
        if a_tag:
            page_link = a_tag["href"]
            all_festivals.append(TempFestival(festival_info[0], festival_info[1], correct_date(festival_info[2]), page_link))

    tasks = [asyncio.create_task(scrape_festival_details(festival)) for festival in all_festivals]
    await asyncio.gather(*tasks)

    filtered_festivals = [] # holds all festivals that need new embeddings
    for festival in all_festivals:
        if await save_temp_festival(festival, db):
            filtered_festivals.append(festival)

    await artist_service.batch_search_artists(50, db)

    # join stage tables with main tables
    await utils.merge_stage_tables(db)

    # generate embeddings and put into table
    if filtered_festivals:
        await llm_service.generate_embeddings(filtered_festivals, db)

    await db.commit()

async def scrape_festival_details(festival: TempFestival):
    """Scrapes detailed information on a festival (artists, tags, dates, description, FAQ)."""
    soup = await utils.get_html(festival.link)

    # Finds all artist elements
    artist_elements = soup.find_all("div", class_="lineupblock")
    artists = [element.get_text(separator='|', strip=True).split("|") for element in artist_elements]
    artists = artists[0] if artists else []
    # TODO: find way to split b2b and vs artists
    festival.artists = artists

    # Finds all tag elements
    tag_elements = soup.find_all("span", class_="heading-breadcrumb")
    tags = [element.get_text(separator='|', strip=True).split("|") for element in tag_elements]
    if tags:
        tags = tags[0]
    festival.tags = tags

    # Processes proper dates
    start_date, end_date = parse_festival_date(festival.date)
    is_cancelled = start_date is None
    if is_cancelled:
        festival.artists = []
    festival.start_date = start_date
    festival.end_date = end_date
    festival.cancelled = is_cancelled

    # Finds MFW descriptions
    scene = soup.find("div", class_="hubscene")
    festival.description = scene.get_text(strip=True) if scene else "There is no description for this festival."

    # Finds FAQ section
    hubtitle = soup.find("div", class_="hubtitle", string="Frequently Asked Questions")
    if hubtitle:
        faq_paragraphs = []
        for sibling in hubtitle.find_next_siblings():
            if sibling.name == "p":
                faq_paragraphs.append(sibling)
            else:
                break

        qa = ""
        for p in faq_paragraphs:
            question_tag = p.find("span")
            question = question_tag.get_text(strip=True) if question_tag else ""

            full_text = p.get_text(" ", strip=True)
            answer = full_text.replace(question, "", 1).strip()

            qa += question + " "
            qa += answer + " "

        festival.faq = qa
    else:
        festival.faq = "No frequently asked questions."

async def save_temp_festival(festival: TempFestival, db: AsyncSession):
    """
    Saves a festival object to the staging table, if it needs an update or does not exist.
    Returns True if the festival was updated/inserted, False if not.
    """
    result = await db.execute(select(Festival).where(Festival.name == festival.name))
    existing_festival = result.scalars().first()

    # check if festival needs to be updated
    # TODO: might need to check if artists updated too
    if existing_festival:
        if existing_festival.cancelled == festival.cancelled and existing_festival.artists:
            return False

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

    return True

def parse_festival_date(date_str: str):
    """Parses start and end dates from single string."""
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