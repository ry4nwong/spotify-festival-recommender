# For all interactions between API and database

from app.models import db
from app.models import Festival, Artist

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