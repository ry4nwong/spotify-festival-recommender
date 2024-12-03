# import dependencies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import json

import musicbrainzngs 

# create a function that uses a client scraper to scrape through the webpage
def webscrape_all_festivals(all_festivals):
    """runs through all pages of musicfestivalwizard to obtain all US festivals"""
    # given all festivals in database with artist names for now
    artist_genre = {}

    def find_genres(artist_name):
        artist_name = artist_name.lower().replace(' ', '-').replace('&', 'and')

        # use musicbranz api
        musicbrainzngs.set_useragent("spotify_music_recommender project", version = '1')
        artist_id = musicbrainzngs.search_artists(query = artist_name, limit = 1)['artist-list']
        if len(artist_id) == 0:
            return None
        else:
            genre_output = []
            for i in artist_id[0]['tag-list']:
                if i['count'] == 0:
                    continue
                else:
                    genre_output.append(i['name'])

        # use gemini query for Nones

        return genre_output

    
    # loop through all festivals and apply function to find artist genres
    for name,festival in all_festivals['festivals'].items():
        artists_to_search = festival['artists']
        for artist in artists_to_search:
            if artist in artist_genre.keys():
                artist_genre[artist] += find_genres(artist)
            else:
                artist_genre[artist] = find_genres(artist)

    return artist_genre
    
# test festival data 
all_festival = {"festivals": {"APOCALYPSE 2024": {"location": "LONG BEACH, CA", "dates": "NOVEMBER 29- 30, 2024 ", "cancelled": False, 'artists':['Excision', 'Slander', '12th Planet']}, "GIVE THANKS FESTIVAL 2024": {"location": "SAN FRANCISCO, CA", "dates": "NOVEMBER 29- 30, 2024 ", "cancelled": False, 'artists':['Loud Luxury', 'Bijou', 'Florime']}}}

# call function and add to json file
all_festival_output = webscrape_all_festivals(all_festival)
with open('backend/app/routes/data/artist_genre.json', 'w') as output_file:
    json.dump(all_festival_output, output_file)