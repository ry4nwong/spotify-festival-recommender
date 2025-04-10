from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.dependencies import get_db
from app.services import festival_service
import requests
import urllib.parse
import time

data_router = APIRouter(prefix="/data", tags=["Data"])

@data_router.post("/scrape")
async def webscrape_all_festivals(db: AsyncSession = Depends(get_db)):
    """Obtains all US and electronic music festivals from musicfestivalwizard."""
    start_time = time.perf_counter()
    await festival_service.webscrape_all_festivals(db)
    end_time = time.perf_counter()

    return JSONResponse(content={"time": end_time - start_time})

@data_router.get("/test-lastfm")
async def test_lastfm(name: str):
    """Tests the last.fm API for gathering artist genres."""
    url2 = f"https://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist={urllib.parse.quote(name)}&api_key=987e94fc27d8d427dc7f119842b9101e&format=json"

    response = requests.get(url2)
    data = response.json()
    tags_list = data.get("toptags", {}).get("tag", [])
    sorted_tags = sorted(tags_list, key=lambda tag: tag["count"], reverse=True)
    top_tags = [tag["name"] for tag in sorted_tags[:5]]

    return JSONResponse(content={"tags": top_tags})

@data_router.get("/test-mfw")
async def test_mfw(link: str):
    """Tests detailed web scraping for musicfestivalwizard."""
    await festival_service.scrape_scene_faq(link)