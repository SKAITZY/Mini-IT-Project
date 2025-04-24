import os
import sqlite3

connection = sqlite3.connect('example.db')

cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    faculty TEXT,
    interests TEXT,
    bio TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS hangout_invites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER PRIMARY KEY AUTOINCREMENT,
    receiver_id INTEGER PRIMARY KEY AUTOIOINCREMENT,
    description TEXT
)
''')

cursor.execute('''
INSERT INTO users (id, name, email, password, faculty, interests, bio) 
VALUES (?, ?, ?, ?, ?, ?, ?)
''', ('Alice0940', 'Alice', 'alice@yahoo.com', '403242', 'FCI', 'Badminton', 'Game is game.'))

connection.commit()
connection.close()

print("Database setup complete.")