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
 
from user_db import get_user_by_token, rotate_token

app = Flask(__name__)
# TEMPORARY for local testing only -- replace before deploying:
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-before-deploying")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False  # flip to True once running on https://
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")

def login_required(view_func):
    """Blocks a route unless someone is logged in. Redirects to a
    'you need a link' page instead of showing an error."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("no_access"))
        return view_func(*args, **kwargs)
    return wrapped