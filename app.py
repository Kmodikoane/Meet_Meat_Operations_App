from flask import Flask, request, jsonify
import sqlite3
import os

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
