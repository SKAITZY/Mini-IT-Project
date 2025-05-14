"""
Database initialization script
------------------------------
Run this script to recreate the database with the correct schema.
"""
from flask import Flask
from extensions import db, init_extensions
from config import Config
from models import User, Customisation
import os
import time

# Create a Flask app instance
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
init_extensions(app)

def init_db():
    print("Starting database initialization...")
    time.sleep(0.5)
    
    # Check the instance directory
    instance_dir = os.path.join(os.getcwd(), 'instance')
    print(f"Instance directory: {instance_dir}")
    time.sleep(0.5)
    
    # Print database configuration
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"Database URI: {db_uri}")
    time.sleep(0.5)
    
    # Clean up all database files in the instance directory
    if os.path.exists(instance_dir):
        print(f"Instance directory found at: {instance_dir}")
        db_files = [f for f in os.listdir(instance_dir) if f.endswith('.db')]
        print(f"Found database files: {db_files}")
        time.sleep(0.5)
        
        for db_file in db_files:
            db_path = os.path.join(instance_dir, db_file)
            try:
                os.remove(db_path)
                print(f"Removed database file: {db_path}")
            except Exception as e:
                print(f"Error removing database file {db_path}: {e}")
            time.sleep(0.5)
    else:
        print(f"No instance directory found at: {instance_dir}")
        os.makedirs(instance_dir, exist_ok=True)
        print(f"Created instance directory: {instance_dir}")
        time.sleep(0.5)
    
    # Also check for database files in the current directory
    print("Checking for database files in current directory...")
    time.sleep(0.5)
    current_dir_db_files = [f for f in os.listdir('.') if f.endswith('.db')]
    if current_dir_db_files:
        print(f"Found database files in current directory: {current_dir_db_files}")
        for db_file in current_dir_db_files:
            try:
                os.remove(db_file)
                print(f"Removed database file from current directory: {db_file}")
            except Exception as e:
                print(f"Error removing database file {db_file}: {e}")
            time.sleep(0.5)
    
    print("Creating database tables...")
    time.sleep(0.5)
    
    # Create the database tables
    with app.app_context():
        db.create_all()
        table_names = db.metadata.tables.keys()
        print(f"Created new database with tables: {', '.join(table_names)}")
        time.sleep(0.5)
        
        # Check table structure
        for table_name in table_names:
            table = db.metadata.tables[table_name]
            cols = [c.name for c in table.columns]
            print(f"Table: {table.name}, Columns: {cols}")
            time.sleep(0.5)
        
        print("Database initialized successfully!")
        time.sleep(0.5)
        
        # Print where database files should be
        print(f"Current working directory: {os.getcwd()}")
        time.sleep(0.5)
        
        instance_db_path = os.path.join(instance_dir, 'jomgather.db')
        if os.path.exists(instance_db_path):
            print(f"Database file found at: {instance_db_path}")
        else:
            print(f"WARNING: Database file not found at expected location: {instance_db_path}")
        
        time.sleep(1)  # Final pause to ensure all output is captured
    
    print("Database initialization complete!")

if __name__ == "__main__":
    init_db() 