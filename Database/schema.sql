CREATE TABLE IF NOT EXISTS gathering (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    gathering_type TEXT NOT NULL,
    faculty TEXT NOT NULL,
    year_semester TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    location TEXT NOT NULL,
    max_participants INTEGER NOT NULL,
    description TEXT NOT NULL,
    target_audience TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id)
);