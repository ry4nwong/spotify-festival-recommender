from shared.db_models import db, Tag

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