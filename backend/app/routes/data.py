# For web scraper.
# import dependencies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import musicbrainzngs 
import google.generativeai as genai
import time
import ast
import json
import os

from datetime import datetime
from flask import Blueprint, jsonify
from app.services.db_service import save_festivals, query, cleanup_past_festivals

data_blueprint = Blueprint('data', __name__)

def new_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--blink-settings=imagesEnabled=false")

    # for selenium stealth
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    new_driver = webdriver.Chrome(options=options)
    stealth(new_driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )
    return new_driver

# create a function that uses a client scraper to scrape through the webpage
# wrapped in flask API call
@data_blueprint.route('/scrape-mfw', methods=['GET'])
def webscrape_all_festivals():
    """runs through all pages of musicfestivalwizard to obtain all US festivals"""
    cleanup_past_festivals()
    all_festivals = {}
    page_count = 1    

    # first page has diff url
    driver = new_webdriver()
    festival_url = "https://www.musicfestivalwizard.com/all-festivals/?festival_guide=us-festivals&festivalgenre=electronic&festivaltype&month&festival_size&festival_length&company#038;festivalgenre=electronic&festivaltype&month&festival_size&festival_length&company"
    driver.get(festival_url)

    # loop until a page without page numbers
    while len(driver.find_elements(By.CLASS_NAME, "page-numbers")) != 0:
    # for i in range(1):
        # pause to allow loading
        time.sleep(1)
        elements = driver.find_elements(By.CLASS_NAME, "entry-title.search-title")
        for element in elements:
            if len(element.text) < 1:
                continue
            else:
                festival_info = str(element.text).split('\n')
                # Skips over advertisements
                print(festival_info[0])
                if "ADVERTISEMENT" in festival_info[0]:
                    continue
                page_link = element.find_elements(By.TAG_NAME, "a")[0]
                artists, tags = webscrape_festival_info(page_link.get_attribute("href"))
                try:
                    correct_date = lambda x: x.split('/')[0] if '/' in x else x
                    start_date, end_date = parse_festival_date(correct_date(festival_info[2]))
                    if_cancelled = lambda x: True if 'CANCELLED' in x else False
                    is_cancelled = if_cancelled(festival_info[2])
                    if is_cancelled:
                        artists = []
                    all_festivals[festival_info[0]] = {
                        'location': festival_info[1], 
                        'start_date': start_date,
                        'end_date': end_date,
                        'cancelled': is_cancelled, 
                        'artists': artists, 
                        'tags': tags
                    }
                except:
                    continue

        time.sleep(2)
        driver.quit()
        page_count += 1
        festival_url = f"https://www.musicfestivalwizard.com/all-festivals/page/{page_count}/?festival_guide=us-festivals&festivalgenre=electronic&festivaltype&month&festival_size&festival_length&company#038;festivalgenre=electronic&festivaltype&month&festival_size&festival_length&company"
        driver = new_webdriver()
        driver.get(festival_url)
    
    time.sleep(2)
    driver.quit()

    # save to database
    save_festivals(all_festivals)
    print('saved to database successfully!')
    return jsonify(all_festivals)

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

# function that scrapes all artist genre info given list of artists
# @data_blueprint.route('/scrape-genres', methods=['GET'])
def all_artist_genre(all_artists):
    artist_genre = {}
    gemini_call_limit = 0

    # loop through all festivals and apply function to find artist genres
    for artist in all_artists:
        output = webscrape_artist_genre(artist, gemini_call_limit)
        artist_genre[artist] = output[0] if artist not in artist_genre.keys() else artist_genre[artist] + output[0]
        gemini_call_limit += output[1]

    return artist_genre

# Helper function to gather artist and tag information
def webscrape_festival_info(festival_href):
    driver = new_webdriver()
    driver.get(festival_href)
    
    time.sleep(1)

    # find all artist names
    artists = driver.find_elements(By.CLASS_NAME, "lineupblock")
    artist_list = []
    if artists:
        artist_list = artists[0].text.split('\n')
    
    # find all tags
    tags = []
    tag_class = driver.find_elements(By.CLASS_NAME, "heading-breadcrumb")[1]
    tag_list = tag_class.find_elements(By.TAG_NAME, "a")
    for tag in tag_list:
        tags.append(tag.text)

    time.sleep(2)

    driver.quit()
    return artist_list, tags

def webscrape_artist_genre(artist_name, gemini_call_limit):
    # function that finds artist genres based on name
    artist_name = artist_name.lower().replace(' ', '-').replace('&', 'and')

    # use musicbranz api
    musicbrainzngs.set_useragent("spotify_music_recommender project", version = '1')
    artist_id = musicbrainzngs.search_artists(query = artist_name, limit = 1)['artist-list']
    print(artist_name)
    if len(artist_id) == 0:
            return [], 0
       
    genre_output = []
    if 'tag-list' in artist_id[0]:
        # genres contain upvotes, only take upvoted genres
        for i in artist_id[0]['tag-list']:
            if i['count'] == 0:
                continue
            else:
                genre_output.append(i['name'])

    # # use gemini for artists that are not found
    # if len(genre_output) == 0:
    #     # api call limit 15 per minute
    #     time.sleep(5)
    #     genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    #     model = genai.GenerativeModel("gemini-1.5-flash")
    #     response = model.generate_content(f'Give me the edm genres in just a python list format for this artist: {artist_name}').text
    #     print(response)
    #     response = response.replace('`', '').split('=', 1)[1].strip()
    #     genre_output = ast.literal_eval(response)

    # if gemini_call_limit > 14:
    #     # wait 1 minute for limit to pass
    #     time.sleep(60)
        
    # increments gemini call count
    return genre_output, 1

# function that returns all festivals in database
@data_blueprint.route('current-festivals', methods=['GET'])
def get_current_festivals():
    return query("FESTIVALS")

# function that returns all artists in database
@data_blueprint.route('current-artists', methods=['GET'])
def get_current_artists():
    return query("ARTISTS")

# function that returns all artists in database
@data_blueprint.route('current-tags', methods=['GET'])
def get_current_tags():
    return query("TAGS")


@data_blueprint.route('/test', methods=['GET'])
def test_query():
    driver = new_webdriver()
    driver.get("https://www.musicfestivalwizard.com")
    print(driver.page_source)
    driver.quit()