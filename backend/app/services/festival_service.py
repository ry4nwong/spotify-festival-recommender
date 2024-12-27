# For all interactions between API and database

from app.models import db, Festival, Artist, Tag
from sqlalchemy import text
from datetime import date, datetime
from app.services.artist_service import save_artist_genre, create_or_get_artist
from app.services.tag_service import create_or_get_tag

# Function to persist festivals in database and link artists/tags
def save_festivals(festivals):
    for name, data in festivals.items():
        new_artists = []
        festival_entry = Festival(
            name = name,
            location = data['location'],
            cancelled = data['cancelled'],
            start_date = data['start_date'],
            end_date = data['end_date']
        )

        for artist in data['artists']:
            # accounts for b2b appearances (ex. Slander B2B Dimension)
            for each_artist in artist.split(' B2B '):
                new_artist, exists = create_or_get_artist(each_artist)
                if not exists:
                    new_artists.append(new_artist.name)
                # Create link, automatically inputted into intermediate table
                if new_artist not in festival_entry.artists:
                    festival_entry.artists.append(new_artist)
        
        for tag in data['tags']:
            new_tag = create_or_get_tag(tag)
            
            # Create link
            festival_entry.tags.append(new_tag)
        
        db.session.add(festival_entry)
        save_artist_genre(new_artists)
        db.session.commit()

# Saves ONE festival to db
def save_festival(festival_entry):
    new_artists = []
    festival, artists_added = check_festival(festival_entry['name'])
    # Adds a new festival if it does not exist
    if festival is None:
        festival = Festival(
            name = festival_entry['name'],
            location = festival_entry['location'],
            cancelled = festival_entry['cancelled'],
            start_date = festival_entry['start_date'],
            end_date = festival_entry['end_date']
        )

        for tag in festival_entry['tags']:
            new_tag = create_or_get_tag(tag)
            
            # Create link
            festival.tags.append(new_tag)

    # Checks if artists updated
    if not artists_added:
        for artist in festival_entry['artists']:
            # accounts for b2b appearances (ex. Slander B2B Dimension)
            for each_artist in artist.split(' B2B '):
                new_artist, exists = create_or_get_artist(each_artist)
                if not exists:
                    new_artists.append(new_artist.name)
                # Create link, automatically inputted into intermediate table
                if new_artist not in festival.artists:
                    festival.artists.append(new_artist)
        
        save_artist_genre(new_artists)

    db.session.add(festival)
    db.session.commit()

# Helper function to get existing tables in database
def query(table = "FESTIVALS"):
    try:
        sql_query = f"SELECT * FROM {table}"
        result = db.session.execute(text(sql_query))
        rows = [dict(row) for row in result.mappings()]
        return rows
    except:
        return "Error executing query: " + sql_query
    
# Function to remove all past festivals
def cleanup_past_festivals():
    try:
        today = date.today()

        past_festivals = Festival.query.filter(Festival.end_date < today).all()

        for festival in past_festivals:
            festival.artists.clear()
            festival.tags.clear()
            db.session.delete(festival)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred during cleanup: {e}")

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

# Returns festival if exists AND if artists already added
# returns festival (object), artists_added (boolean)
def check_festival(festival_name):
    festival = Festival.query.filter_by(name=festival_name).first()
    artists_added = bool(festival.artists) if festival is not None else False

    return festival, artists_added