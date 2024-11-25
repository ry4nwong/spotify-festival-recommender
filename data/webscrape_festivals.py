# import dependencies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import json

# create a function that uses a client scraper to scrape through the webpage
def webscrape_all_festivals(festival_url):
    """runs through all pages of musicfestivalwizard to obtain all festivals"""
    all_festivals = {}
    page_count = 1

    # first page has diff url
    driver = webdriver.Chrome()
    festival_url = "https://www.musicfestivalwizard.com/all-festivals/"
    driver.get(festival_url)

    # loop until a page without page numbers
    while True and len(driver.find_elements(By.CLASS_NAME, "page-numbers")) != 0: 
        if page_count != 1:
            festival_url = f"https://www.musicfestivalwizard.com/all-festivals/page/{page_count}/"
        driver = webdriver.Chrome()
        driver.get(festival_url)
        elements = driver.find_elements(By.CLASS_NAME, "entry-title.search-title")
        for element in elements:
            if len(element.text) <= 1:
                continue
            else:
                all_festivals[element.text] = 1
        page_count += 1
        time.sleep(3)
    return all_festivals

# call function and add to json file
all_festival_output = webscrape_all_festivals("https://www.musicfestivalwizard.com/all-festivals/")

with open('data/all_festivals.json', 'w') as output_file:
    json.dump(all_festival_output, output_file)