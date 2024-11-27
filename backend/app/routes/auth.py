from flask import Blueprint, redirect, request, session, current_app
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from dotenv import load_dotenv
import os


auth_blueprint = Blueprint('auth', __name__)

# Initialize Spotify OAuth with configuration
def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope="user-library-read playlist-modify-private"
    )

# Gain Spotify access token
@auth_blueprint.route('/login', methods=['GET'])
def login():
    sp_oauth = get_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Callback from Spotify login
@auth_blueprint.route('/callback', methods=['GET'])
def callback():
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_access_token(request.args["code"])
    session["token_info"] = token_info
    # Should navigate to next page, return for now
    return token_info