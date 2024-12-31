from app import db
from shared.db_models import Festival, Artist, Tag

from flask import Blueprint, jsonify

db_blueprint = Blueprint('db', __name__)

@db_blueprint.route('/festivals', methods=['GET'])
def get_festivals():
    festivals = Festival.query.all()

    festival_list = [
            {
                "id": festival.id,
                "name": festival.name,
                "location": festival.location,
                "date": festival.start_date
            }
            for festival in festivals
        ]
    
    return jsonify(festival_list), 200