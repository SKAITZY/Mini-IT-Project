from app import app, db
from models import User, Customisation, Connection, Message, Gathering, GatheringParticipant, GatheringMessage

# Use application context
with app.app_context():
    # This will create all tables that don't exist and add any missing columns
    db.create_all()
    print("Database schema updated!") 