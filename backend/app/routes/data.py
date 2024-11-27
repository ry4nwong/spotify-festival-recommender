# For web scraper.
# import dependencies
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# create a function that uses a client scraper to scrape through the webpage
def webscrape_all_festivals(festival_url):
    """runs through all pages of musicfestivalwizard to obtain all US festivals"""
    all_festivals = {'festivals':{}}
    page_count = 1

    # first page has diff url
    driver = webdriver.Chrome()
    festival_url = "https://www.musicfestivalwizard.com/festival-guide/us-festivals/"
    driver.get(festival_url)

    # loop until a page without page numbers
    while True and len(driver.find_elements(By.CLASS_NAME, "page-numbers")) != 0: 
        if page_count != 1:
            festival_url = f"https://www.musicfestivalwizard.com/festival-guide/us-festivals/page/{page_count}/"
        driver = webdriver.Chrome()
        driver.get(festival_url)

        # pause to allow loading
        time.sleep(1)
        elements = driver.find_elements(By.CLASS_NAME, "entry-title.search-title")
        for element in elements:
            if len(element.text) < 1:
                continue
            else:
                festival_info = str(element.text).split('\n')
                try:
                    correct_date = lambda x: x.split('/')[0] if '/' in x else x
                    date = correct_date(festival_info[2])
                    if_cancelled = lambda x: True if 'CANCELLED' in x else False
                    is_cancelled = if_cancelled(festival_info[2])
                    all_festivals['festivals'][festival_info[0]] = {'location': festival_info[1], 'dates': date, 'cancelled': is_cancelled}
                except:
                    continue
        page_count += 1
        time.sleep(3)
    return all_festivals

# call function and add to json file
all_festival_output = webscrape_all_festivals("https://www.musicfestivalwizard.com/festival-guide/us-festivals/")

with open('backend/app/routes/data/all_festivals.json', 'w') as output_file:
    json.dump(all_festival_output, output_file)