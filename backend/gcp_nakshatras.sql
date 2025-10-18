CREATE TABLE nakshatras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    lord TEXT NOT NULL,
    deity TEXT NOT NULL,
    nature TEXT NOT NULL,
    guna TEXT NOT NULL,
    description TEXT NOT NULL,
    characteristics TEXT NOT NULL,
    positive_traits TEXT NOT NULL,
    negative_traits TEXT NOT NULL,
    careers TEXT NOT NULL,
    compatibility TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);