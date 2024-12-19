from app.models import db
from app.models import Festival, Artist, Tag, festival_tags

from sqlalchemy.orm import aliased

from flask import Blueprint, jsonify, request

db_blueprint = Blueprint('db', __name__)

# Returns all festivals
@db_blueprint.route('/festivals', methods=['GET'])
def get_festivals():
    festivals = Festival.query.all()

    festival_list = [
        {
            "id": festival.id,
            "name": festival.name,
            "location": festival.location,
            "date": festival.date,
            "tags": [{"id": tag.id, "name": tag.name} for tag in festival.tags]
        }
        for festival in festivals
    ]
    
    return jsonify(festival_list), 200

# Returns festival by ID
@db_blueprint.route('/festivals/<int:id>', methods=['GET'])
def get_festival(id):
    festival = Festival.query.filter_by(id=id).first()

    # id not found
    if not festival:
        return jsonify({"error": f"Festival with ID {id} not found"}), 404
    
    festival_data = {
        "id": festival.id,
        "name": festival.name,
        "location": festival.location,
        "date": festival.date,
        "artists": [{"id": artist.id, "name": artist.name} for artist in festival.artists],
        "tags": [{"id": tag.id, "name": tag.name} for tag in festival.tags]
    }

    return jsonify(festival_data), 200

# Returns all artists
@db_blueprint.route('/artists', methods=['GET'])
def get_artists():
    artists = Artist.query.all()

    artist_list = [
        {
            "id": artist.id,
            "name": artist.name,
            "tags": [{"id": tag.id, "name": tag.name} for tag in artist.genres]
        }
        for artist in artists
    ]
    
    return jsonify(artist_list), 200

# Returns artist by ID
@db_blueprint.route('/artists/<int:id>', methods=['GET'])
def get_artist(id):
    artist = Artist.query.filter_by(id=id).first()

    # id not found
    if not artist:
        return jsonify({"error": f"Artist with ID {id} not found"}), 404
    
    artist_data = {
        "id": artist.id,
        "name": artist.name,
        "tags": [{"id": tag.id, "name": tag.name} for tag in artist.genres]
    }

    return jsonify(artist_data), 200

# Queries festivals by tag
@db_blueprint.route('/festivals/by-tags', methods=['GET'])
def get_festivals_by_tags():
    tag_names = request.args.getlist('tags')
    if not tag_names:
        return jsonify({"error": "No tags provided"}), 400
    
    tag = db.session.query(Tag).filter(Tag.name == "electronic").first()

    if tag:
        festivals = tag.festivals  # Access related festivals through the relationship
        print(festivals)
    else:
        print("Tag not found.")
    
    festivals = (
        db.session.query(Festival)
        .filter(Festival.tags.any(Tag.name.in_(tag_names)))  # Use the tags relationship
        .distinct()
        .all()
    )   

    # Format the result into a JSON response
    response = [
        {
            "id": festival.id,
            "name": festival.name,
            "location": festival.location,
            "date": festival.date,
            "cancelled": festival.cancelled,
            "tags": [tag.name for tag in festival.tags]
        }
        for festival in festivals
    ]
    
    return jsonify(response)

# Queries artists by festival

# Queries Tags by artist

# Queries Festivals by artist

# Queries tags by festival