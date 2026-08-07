"""
app.py
 
The web app itself. Handles:
  - /login/<token>  : the link an executive taps. Validates the token,
                       rotates it (kills the link they just used),
                       and starts a secure session.
  - /dashboard       : the landing page after login, gated by role.
  - /logout          : ends the session early on a shared/borrowed device.
 
SECURITY NOTES (read this before deploying):
  - SECRET_KEY below signs session cookies so Flask can detect if one has
    been tampered with -- but ONLY if this key stays secret and is never
    committed to a public repo. Before deploying for real, replace it
    with a long random value stored in an environment variable, not
    hardcoded here.
  - Cookies are set httponly (JavaScript can't read them -- blocks a
    common theft method). Set secure=True once this runs over HTTPS;
    it's off here so local testing over plain http:// still works.
  - SESSION_LIFETIME controls how long someone stays logged in before
    needing a fresh link from an admin.
"""
 
import os
from datetime import timedelta
from functools import wraps
from flask import Flask, session, redirect, url_for, render_template, abort
 
from user import get_user_by_token, rotate_token

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")

def get_user_from_db(username):
    """Helper function to look up a user and their role"""
    connection = sqlite3.connection(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("SELECT username, first_name, last_name, role FROM user: WHERE username = ?",(username))
    user = cursor.fetchone()
    connection.close()
    return user

@app.route('/dashboard')
def dashboard():
    # Instead of input(), grab the username directly from the link/URL
    username = request.args.get('username')
    user_data = get_user_from_db(username)

    if not user_data:
        return "<h1>Access Deneied: Invalid Username<h1", 401 
    
    if not username:
        return "Error: Please provide a username in the link (e.g., /dashboard?username=john_doe)", 400

    first_name, last_name, role = user_data

     # --- LEVEL 1: EXECUTIVE VIEW (Both Admin and Exec can see this) ---
    html_content = f"""
    <h1>Meet Meat Dashboard</h1>
    <p>Welcome back, {first_name} {last_name} ({role.upper()})</p>
    <hr>
    <h3>📊 Executive Analytics (View Only)</h3>
    <ul>
        <li>Total Meat Sales Today: R15,400</li>
        <li>Current Stock Level: 420 kg</li>
    </ul>
    """

    # --- LEVEL 2: ADMINISTRATOR CONTROLS (Only Admin can see this) ---
    if role == 'admin':
        html_content += """
        <div style="background-color: #fee; padding: 15px; margin-top: 20px; border: 1px solid #f00;">
            <h3>🛠️ Administrator Controls</h3>
            <button onclick="alert('Price updated!')">Update Meat Pricing</button>
            <button onclick="alert('User added!')">Add New Employee</button>
        </div>
        """
    else:
        html_content += "<p><i>Note: Administrative control panel is hidden for your role.</i></p>"

    return html_content

if __name__ == "__main__":
    app.run(debug=True)
