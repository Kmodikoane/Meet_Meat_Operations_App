import sqlite3
import os
import secrets
from email.message import EmailMessage

# This forces Python to look in the script's actual directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.sql")

# --- Email delivery configuration ---------------------------------------
# Read from environment variables, never hardcoded -- these are secrets.
# On Windows (PowerShell), set them per session with:
#   $env:MEATMEET_EMAIL = "youraddress@gmail.com"
#   $env:MEATMEET_EMAIL_APP_PASSWORD = "your16charapppassword"
# If they're not set, send_login_email() falls back to just printing the
# link to the console -- so you can keep testing everything else even
# before real email is wired up.
EMAIL_ADDRESS = os.environ.get("MEATMEET_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MEATMEET_EMAIL_APP_PASSWORD")
SITE_BASE_URL = os.environ.get("MEATMEET_BASE_URL", "http://127.0.0.1:5000")

def init_db():
    """Builds the database using the schema.sql blueprint."""
    # Ensure the SQL file exists before running
    if not os.path.exists(SCHEMA_FILE):
        print(f"Error: {SCHEMA_FILE} not found! Please create it first.")
        return

    # Connect and execute the SQL script
    connection = sqlite3.connect(DB_FILE)
    with open(SCHEMA_FILE, "r") as f:
        connection.executescript(f.read())
    
    connection.commit()
    connection.close()
    print("Database initialised successfully!")

def add_user(username, email, first_name, last_name, role, phone_number=None):
    """
    Creates a new user with a fresh, unique login token and inserts them.
    phone_number is optional for now -- it's stored ready for WhatsApp
    delivery once that's built, but nothing reads it yet.
    """
    clean_first_name = first_name.strip().title()
    clean_last_name = last_name.strip().title()

    token = secrets.token_urlsafe(32)

    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    try:
        cursor.execute(
            """INSERT INTO users (username, email, phone_number, first_name, last_name, role, token)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (username, email, phone_number, clean_first_name, clean_last_name, role, token),
        )
        connection.commit()
        print(f"User '{username}' added successfully.")
        print(f"  Login link token: {token}")
        print(f"  (send them: {SITE_BASE_URL}/login/{token})")
        return token
    except sqlite3.IntegrityError as e:
        print(f"Error: could not add '{username}' -- {e}")
        return None
    finally:
        connection.close()



def add_user(username, email, first_name, last_name, role):
    """Example Python function to insert a new user."""

    clean_first_name = first_name.strip().title()  # Converts "kgomo" or "KGOMO" to "Kgomo"
    clean_last_name = last_name.strip().title()    # Converts "smith" to "Smith"

    token = secrets.token_urlsafe(32)

    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, email, first_name, last_name, role, token) VALUES (?, ?, ?, ?, ?, ?)", 
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
        "SELECT user_id, username, email, first_name, last_name, role, token FROM users WHERE token = ?",
        (token,),
    )
    row = cursor.fetchone()
    connection.close()
    if row is None:
        return None
    keys = ("user_id", "username", "email", "first_name", "last_name", "role", "token")
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
    cursor.execute("UPDATE users SET token = ? WHERE user_id = ?", (new_token, user_id))
    connection.commit()
    connection.close()
    return new_token


def check_users():
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    
    # Fetch everyone in the table
    cursor.execute("SELECT * FROM users;")
    rows = cursor.fetchall()
    
    print("\n--- Current Users in Database ---")
    for row in rows:
        user_id, username, email, first_name, last_name, role, token = row

        print(f"User ID: {user_id} | {first_name} {last_name} | Username: {username}"
              f"{email} | role : {role} | token : {token[:8]}")
    connection.close()

if __name__ == "__main__":
    init_db()
    
    print("\n1. Add a new user")
    print("2. List all users")
    choice = input("Choose an option (1/2): ").strip()

    if choice == "1":
        add_user_interactive()
    elif choice == "2":
        check_users()
    else:
        print("No valid option selected.")
    check_users() # <-- Add this line to print the results

