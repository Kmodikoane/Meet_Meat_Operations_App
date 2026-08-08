"""
app.py

The web app itself. Handles:
  - /login/<token>   : the link an executive taps. Validates the token,
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

from user_db import get_user_by_token, rotate_token

app = Flask(__name__)

# TEMPORARY for local testing only -- replace before deploying:
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-before-deploying")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False  # flip to True once running on https://
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)


def login_required(view_func):
    """Blocks a route unless someone is logged in. Redirects to a
    'you need a link' page instead of showing an error."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session or not session.get("user_id"):
            return redirect(url_for("no_access"))
        return view_func(*args, **kwargs)
    return wrapped


def role_required(*allowed_roles):
    """Blocks a route unless the logged-in user's role is in allowed_roles.
    Use like: @role_required('admin')  -- only admins can reach it."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                abort(403)  # Forbidden -- logged in, but not allowed here
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


@app.route("/login/<token>")
def login(token):
    user = get_user_by_token(token)
    if user is None:
        # Don't say WHY it failed (expired vs never existed vs already
        # used) -- that tells an attacker too much. Same generic message
        # either way.
        return render_template("login_failed.html"), 401

    # Rotate the token immediately: the link they just clicked is now dead.
    rotate_token(user["user_id"])

    # Start the session
    session.permanent = True
    session["user_id"] = user["user_id"]
    session["role"] = user["role"]
    session["display_name"] = f"{user['first_name']} {user['last_name']}"

    return redirect(url_for("dashboard"))


@app.route("/no-access")
def no_access():
    return render_template("no_access.html")


@app.route("/dashboard")
@login_required
def dashboard():
    # Identity comes from the session (set during login), never from
    # anything in the URL or a form field -- the session cookie is signed
    # by Flask using SECRET_KEY, so it can't be edited by hand the way a
    # URL parameter can.
    display_name = session["display_name"]
    role = session["role"]

    html_content = f"""
    <h1>Meet Meat Dashboard</h1>
    <p>Welcome back, {display_name} ({role.upper()})</p>
    <hr>
    <h3>Executive Analytics (View Only)</h3>
    <ul>
        <li>Total Meat Sales Today: R15,400</li>
        <li>Current Stock Level: 420 kg</li>
    </ul>
    """

    if role == "admin":
        html_content += """
        <div style="background-color: #fee; padding: 15px; margin-top: 20px; border: 1px solid #f00;">
            <h3>Administrator Controls</h3>
            <button onclick="alert('Price updated!')">Update Meat Pricing</button>
            <button onclick="alert('User added!')">Add New Employee</button>
        </div>
        """
    else:
        html_content += "<p><i>Note: Administrative control panel is hidden for your role.</i></p>"

    html_content += '<p><a href="/logout">Log out</a></p>'
    return html_content


@app.route("/admin-logs")
@login_required
@role_required("admin", "exec")  # both roles can VIEW the log; @login_required MUST come first
def admin_logs():
    # Real log data comes in the next module -- this proves the route
    # and the role gate work first.
    return render_template("admin_logs.html", display_name=session["display_name"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("no_access"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)