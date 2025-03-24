from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from selenium import webdriver
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from bs4 import BeautifulSoup

async def new_webdriver():
    """Delivers a new webdriver to scrape musicfestivalwizard."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

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

async def get_html(link: str):
    """Gives a BeautifulSoup object from a given link for parsing."""
    driver = await new_webdriver()
    driver.get(link)
    html = driver.page_source
    driver.quit()

    return BeautifulSoup(html, "html.parser")

async def merge_stage_tables(db: AsyncSession):
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