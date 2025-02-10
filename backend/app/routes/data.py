# For web scraper.
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.dependencies import get_db
from app.services.festival_service import save_festival, cleanup_past_festivals, parse_festival_date

from bs4 import BeautifulSoup

data_router = APIRouter(prefix="/data", tags=["Data"])

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

# Semaphore for concurrency limits
async def scraper_semaphore(semaphore, driver, page_link, festival):
    async with semaphore:
        await scrape_festival_details(driver, page_link, festival)

@data_router.get("/scrape-mfw-bs")
async def webscrape_all_festivals(db: AsyncSession = Depends(get_db)):
    """Runs through all pages of musicfestivalwizard to obtain all US festivals."""
    await cleanup_past_festivals()
    all_festivals = {} 
    driver = await new_webdriver()
    semaphore = asyncio.Semaphore(3)
    
    festival_url = "https://www.musicfestivalwizard.com/all-festivals/?festival_guide=us-festivals&festivalgenre=electronic"
    driver.get(festival_url)
    html = driver.page_source
    # driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    
    # Extract festival info and page link
    elements = soup.find_all("div", class_="entry-title search-title")
    festivals = []
    for element in elements:
        festival_info = element.get_text(separator='|', strip=True).split("|")
        a_tag = element.find("a")
        if a_tag:
            page_link = a_tag["href"]
            festivals.append((festival_info, page_link))

    festival_tasks = []

    for festival_info, page_link in festivals:
        if "ADVERTISEMENT" in festival_info[0]:
            continue

        festival_tasks.append(scraper_semaphore(semaphore, driver, page_link, festival_info))
        # await scrape_festival_details(driver, page_link, festival)

    await asyncio.gather(*festival_tasks)

    driver.quit()
    print('Saved to database successfully!')
    return all_festivals


async def scrape_festival_details(driver, page_link, festival_info):
    driver = await new_webdriver()
    driver.get(page_link)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    elements = soup.find_all("div", class_="lineupblock")
    artist_list = [element.get_text(separator='|', strip=True).split("|") for element in elements]
    # Find all artist names
    if artist_list:
        artist_list = artist_list[0]

    # Find all tags
    elements = soup.find_all("span", class_="heading-breadcrumb")
    tag_list = [element.get_text(separator='|', strip=True).split("|") for element in elements]

    try:
        correct_date = lambda x: x.split('/')[0] if '/' in x else x
        start_date, end_date = parse_festival_date(correct_date(festival_info[2]))
        print("Start and end dates:", start_date, end_date)
        is_cancelled = start_date is None

        if is_cancelled:
            artist_list = []

        festival_entry = {
            'name': festival_info[0],
            'location': festival_info[1],
            'start_date': start_date,
            'end_date': end_date,
            'cancelled': is_cancelled,
            'artists': artist_list,
            'tags': tag_list[0]
        }

        await save_festival(festival_entry)
    except Exception as e:
        print(f"❌ Error in scrape_festival_details for {festival_info[0]}: {e}")
        print(f"❌ Festival info: {festival_info}")
        print(f"❌ artist_list: {artist_list}")
        print(f"❌ tag_list: {tag_list}")
        print(page_link)

@data_router.get("/test")
async def scrape_test():
    driver = await new_webdriver()
    driver.get("https://www.musicfestivalwizard.com/all-festivals/page/4/?festival_guide=us-festivals&festivalgenre=electronic&festivaltype&month&festival_size&festival_length&company#038;festivalgenre=electronic&festivaltype&month&festival_size&festival_length&company")

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    elements = soup.find_all("div", class_="entry-title search-title")
    festivals = [element.get_text(separator='|', strip=True).split("|") for element in elements]

    festivals2 = []
    for element in elements:
        festival_info = element.get_text(separator='|', strip=True).split("|")
        a_tag = element.find("a")
        if a_tag:
            page_link = a_tag["href"]
            festivals2.append((festival_info, page_link))



    print(festivals2)