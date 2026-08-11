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

ef get_user_by_email(email):
    """Looks up a user by email (case-insensitive). Used by the
    'request a new link' self-service flow."""
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, username, email, phone_number, first_name, last_name, role, token "
        "FROM users WHERE LOWER(email) = LOWER(?)",
        (email,),
    )
    row = cursor.fetchone()
    connection.close()
    if row is None:
        return None
    keys = ("id", "username", "email", "phone_number", "first_name", "last_name", "role", "token")
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

def send_login_email(to_email, first_name, token):
    """
    Emails a fresh login link. If email credentials aren't configured yet
    (see EMAIL_ADDRESS / EMAIL_APP_PASSWORD above), this just prints the
    link instead -- so the rest of the login flow stays testable without
    needing real email set up first.
    """
    link = f"{SITE_BASE_URL}/login/{token}"

    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        print("[Email not configured -- printing instead]")
        print(f"  To: {to_email}")
        print(f"  Link: {link}")
        return True
        msg = EmailMessage()
    msg["Subject"] = "Your Meat Meet login link"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(
        f"Hi {first_name},\n\n"
        f"Here's your login link for Meat Meet Operations:\n\n{link}\n\n"
        f"This link works once and expires after use -- if you need another, "
        f"request a new one from the login page.\n"
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"Login email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False

def request_new_link(email):
    """
    The self-service 'I need to log back in' flow. Looks up the email,
    and if found, rotates their token and emails them the fresh link.

    Deliberately returns True in EVERY case (found or not) -- the caller
    (the Flask route) should always show the same generic message to the
    person using the form. If we said 'that email isn't registered' for
    unknown emails, it would let someone probe which emails exist in the
    system, which is information they shouldn't be able to fish for.
    """
    user = get_user_by_email(email)
    if user is None:
        print(f"[request_new_link] No user found for {email} -- not revealing this to the caller.")
        return True

    new_token = rotate_token(user["id"])
    send_login_email(user["email"], user["first_name"], new_token)
    return True
    
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

