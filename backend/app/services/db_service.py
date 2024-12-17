# For all interactions between API and database

from app.models import db
from app.models import Festival, Artist, Tag

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
            date = data['date'],
        )

        for artist in data['artists']:
            # accounts for b2b appearances (ex. Slander B2B Dimension)
            for each_artist in artist.split(' B2B '):
                new_artist, exists = create_or_get_artist(each_artist)
                if not exists:
                    new_artists.append(new_artist.name)
                # Create link, automatically inputted into intermediate table
                festival_entry.artists.append(new_artist)
        
        for tag in data['tags']:
            new_tag = create_or_get_tag(tag)
            
            # Create link
            festival_entry.tags.append(new_tag)
        
        db.session.add(festival_entry)
        save_artist_genre(new_artists)
        db.session.commit()

# Function to run web scraper on genre for each artist and persist in database
def save_artist_genre(new_artists):
    from app.routes.data import all_artist_genre
    # Get genres for each new artist
    artist_genres = all_artist_genre(new_artists)

    for artist_name, genre_list in artist_genres.items():
        # Artist should be guaranteed to be stored in db
        artist = Artist.query.filter_by(name=artist_name).first()
    
        for genre_string in genre_list:
            artist.genres.append(create_or_get_tag(genre_string)) 

# Helper function to get or create artist in database
def create_or_get_artist(artist_name):
    existing_artist = Artist.query.filter_by(name=artist_name).first()

    # If artist does not already exist, create new entry
    if not existing_artist:
        new_artist = Artist(name=artist_name)
        exists = False
        db.session.add(new_artist)
    else:
        new_artist = existing_artist
        exists = True

    return new_artist, exists

# Helper function to get or create tag/genre in database
def create_or_get_tag(tag_name):
    existing_tag = Tag.query.filter_by(name=tag_name).first()

    # If tag does not already exist, create new entry
    if not existing_tag:
        new_tag = Tag(name=tag_name)
        db.session.add(new_tag)
    else:
        new_tag = existing_tag
    
    return new_tag



def save_to_db(scraped_data, data_type = 'festival'):
    counter = 1
    if data_type == 'festival':
        for name, vals in scraped_data.items():
            data_entry = Festival(
                id = counter, 
                name = name, 
                artists = vals['artists'], 
                location = vals['location'],
                date = vals['date'],
                tags = vals['tags']
            )
            counter += 1
            db.session.add(data_entry)
            db.session.commit()
    if data_type == 'artists':
        for name, vals in scraped_data.items():
            data_entry = Artist(
                id = counter, 
                name = name, 
                genre = vals # might need to convert to string
            )
            counter += 1
            db.session.add(data_entry)
            db.session.commit()