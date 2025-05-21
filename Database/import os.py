<<<<<<< HEAD
<<<<<<< HEAD
import os
import sqlite3

connection = sqlite3.connect()

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
    status TEXT
)
''')

cursor.execute('''
INSERT INTO users (id, name, email, password, faculty, interests, bio) 
VALUES (?, ?, ?, ?, ?, ?, ?)
''', ('Alice0940', 'Alice', 'alice@yahoo.com', '403242', 'FCI', 'Badminton', 'Game is game.'))

cursor.execute('''
INSERT INTO users (id, sender_id, receiver_id, status TEXT) 
VALUES (?, ?, ?, ?)
''', ('00001', '002', '001', 'ACTIVE'))

connection.commit()
connection.close()

print("Database setup complete.")
=======
=======
>>>>>>> d8e3fcbb015c1439225646655db38ad2ea2f61a5
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



