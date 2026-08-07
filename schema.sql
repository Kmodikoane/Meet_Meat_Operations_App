-- 1. Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL
);

-- 2. Seed the database with the first 2 users
INSERT OR IGNORE INTO users (username, email) VALUES ('john_doe', 'john@example.com');
INSERT OR IGNORE INTO users (username, email) VALUES ('jane_doe', 'jane@example.com');
