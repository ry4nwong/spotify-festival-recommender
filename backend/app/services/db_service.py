# For all interactions between API and database

from app.models import db
from app.models import Festival, Artist, Tag

def save_festivals(festivals):
    for name, data in festivals.items():
        festival_entry = Festival(
            name = name,
            location = data['location'],
            cancelled = data['cancelled'],
            date = data['date'],
        )

        for artist in data['artists']:
            existing_artist = Artist.query.filter_by(name=artist).first()
            # If artist does not already exist, create new entry
            if not existing_artist:
                new_artist = Artist(name=artist)
                db.session.add(new_artist)
            else:
                new_artist = existing_artist
            
            # Create link, automatically inputted into intermediate table
            festival_entry.artists.append(new_artist)
        
        for tag in data['tags']:
            existing_tag = Tag.query.filter_by(name=tag).first()
            # If tag does not already exist, create new entry
            if not existing_tag:
                new_tag = Tag(name=tag)
                db.session.add(new_tag)
            else:
                new_tag = existing_tag
            
            # Create link
            festival_entry.tags.append(new_tag)
        
        db.session.add(festival_entry)
        db.session.commit()


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