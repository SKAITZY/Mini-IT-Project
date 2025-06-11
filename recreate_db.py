from app import app, db
from models import User, Customisation, Connection, Message, Gathering, GatheringParticipant, GatheringMessage
import os

# Check if the database file exists and delete it
db_path = os.path.join(app.instance_path, 'jomgather.db')
if os.path.exists(db_path):
    print(f"Removing existing database at {db_path}")
    os.remove(db_path)
else:
    print(f"No existing database found at {db_path}")

# Use application context
with app.app_context():
    # Create all tables
    db.create_all()
    print("Database recreated successfully!")

    # Create a test user
    test_user = User(
        student_id="12345678",
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    db.session.add(test_user)
    db.session.commit()
    print("Test user created successfully!") 