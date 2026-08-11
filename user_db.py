import sqlite3
import os
import secrets

# This forces Python to look in the script's actual directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.sql")


def init_db():
    """Builds the database using the schema.sql blueprint."""
    if not os.path.exists(SCHEMA_FILE):
        print(f"Error: {SCHEMA_FILE} not found! Please create it first.")
        return

    connection = sqlite3.connect(DB_FILE)
    with open(SCHEMA_FILE, "r") as f:
        connection.executescript(f.read())

    connection.commit()
    connection.close()
    print("Database initialised successfully!")


def add_user(username, email, first_name, last_name, role):
    """
    Creates a new user with a fresh, unique login token and inserts them.
    The token is generated here -- not typed by hand -- because it's the
    actual credential for their magic link. secrets.token_urlsafe is built
    specifically for this (cryptographically random, URL-safe characters).
    """
    clean_first_name = first_name.strip().title()  # "kgomo" / "KGOMO" -> "Kgomo"
    clean_last_name = last_name.strip().title()

    token = secrets.token_urlsafe(32)

    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    try:
        cursor.execute(
            """INSERT INTO users (username, email, first_name, last_name, role, token)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, email, clean_first_name, clean_last_name, role, token),
        )
        connection.commit()
        print(f"User '{username}' added successfully.")
        print(f"  Login link token: {token}")
        print(f"  (send them: https://yoursite.com/login/{token})")
        return token
    except sqlite3.IntegrityError as e:
        print(f"Error: could not add '{username}' -- {e}")
        return None
    finally:
        connection.close()


def get_user_by_token(token):
    """
    Looks up a user by their current token. Used by the login route.
    Returns None if the token doesn't match anyone -- either it was
    never valid, or it's an old token that's already been rotated out.
    """
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, username, email, first_name, last_name, role, token FROM users WHERE token = ?",
        (token,),
    )
    row = cursor.fetchone()
    connection.close()
    if row is None:
        return None
    keys = ("id", "username", "email", "first_name", "last_name", "role", "token")
    return dict(zip(keys, row))


def rotate_token(user_id):
    """
    Replaces a user's token with a brand new one and returns it.

    This is called automatically the moment someone successfully logs in
    with their link -- so the link they just used stops working right
    after. If that link was ever forwarded, screenshotted, or left
    sitting in a message somewhere, it's now dead. This is also the
    function an admin calls manually to issue someone a fresh link if
    their old one might have been exposed, or they lost their phone.
    """
    new_token = secrets.token_urlsafe(32)
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET token = ? WHERE id = ?", (new_token, user_id))
    connection.commit()
    connection.close()
    return new_token


def check_users():
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute("SELECT id, username, email, first_name, last_name, role, token FROM users;")
    rows = cursor.fetchall()

    print("\n--- Current Users in Database ---")
    for row in rows:
        user_id, username, email, first_name, last_name, role, token = row
        # Only show the first 8 characters of the token when printing --
        # it's a credential, not something to casually paste into logs.
        print(f"ID: {user_id} | {first_name} {last_name} ({username}) | "
              f"{email} | role={role} | token={token[:8]}...")
    connection.close()


if __name__ == "__main__":
    init_db()
    check_users()
