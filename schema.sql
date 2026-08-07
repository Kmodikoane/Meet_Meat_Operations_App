-- 1. Create the users table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    
      -- Enforce required First Name (No empty strings allowed)
    first_name TEXT NOT NULL CHECK(length(trim(first_name)) > 0),
    
    -- Enforce required Surname (No empty strings allowed)
    last_name TEXT NOT NULL CHECK(length(trim(last_name)) > 0),
    role TEXT NOT NULL CHECK(role IN ('admin', 'exec')),
    token TEXT NOT NULL UNIQUE
);


-- 2. Seed the database with the first 2 users
INSERT OR IGNORE INTO users (username, email, first_name, last_name, role, token) 
VALUES ('KModikoane', 'motsomodikoane@gmail.com', 'Kgomotso', 'Modikoane', 'admin', 'TKN_placeholder1');

INSERT OR IGNORE INTO users (username, email, first_name, last_name, role, token) 
VALUES ('Kgothatso@MeetMeat', 'kgomotso.it.modikoane@gmail.com', 'Kgothatso', 'MeetMeat', 'exec','TKN_placeholder2')
;