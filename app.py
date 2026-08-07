from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")

@app.route('/dashboard')
def dashboard():
    # Instead of input(), grab the username directly from the link/URL
    username = request.args.get('username')
    
    if not username:
        return "Error: Please provide a username in the link (e.g., /dashboard?username=john_doe)", 400

    # Query the SQLite database
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    connection.close()

    if user:
        # If user exists, show dashboard data
        return f"<h1>Welcome to the Meat Meat Dashboard, {user[1]}!</h1><p>Email: {user[2]}</p>"
    else:
        return "<h1>User not found</h1>", 404

if __name__ == "__main__":
    app.run(debug=True)
