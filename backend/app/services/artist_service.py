from shared.db_models import Artist, db
from app.services.tag_service import create_or_get_tag

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