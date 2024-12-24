# For all interactions between API and database

from app.models import db, Festival, Artist, Tag
from sqlalchemy import text
from datetime import date
from artist_service import save_artist_genre, create_or_get_artist
from tag_service import create_or_get_tag

# Function to persist festivals in database and link artists/tags
def save_festivals(festivals):
    for name, data in festivals.items():
        # Does not add duplicates
        festival_exists = Festival.query.filter_by(name=name).first()
        if festival_exists:
            continue

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