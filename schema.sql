CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    phone_number TEXT,
    first_name TEXT NOT NULL CHECK(length(trim(first_name)) > 0),
    last_name TEXT NOT NULL CHECK(length(trim(last_name)) > 0),
    role TEXT NOT NULL CHECK(role IN ('admin', 'exec')),
    token TEXT NOT NULL UNIQUE
);

-- -- 2. Seed the database with the first 2 users
-- INSERT OR IGNORE INTO users ( username, email, first_name, last_name, role) 
-- VALUES ('KModikoane', 'motsomodikoane@gmail.com', 'Kgomotso', 'Modikoane', 'admin');

-- INSERT OR IGNORE INTO users (username, email, first_name, last_name, role) 
-- VALUES ('Kgothatso@MeetMeat', 'kgomotso.it.modikoane@gmail.com', 'Kgothatso', 'MeetMeat', 'exec')
-- ;