from spotipy.oauth2 import SpotifyOAuth
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
import requests
import os

async def get_spotify_oauth():
    """Initializes Spotify OAUTH with configuration."""
    return SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope="user-library-read playlist-modify-private"
    )

async def get_user_data(access_token: str):
    """Fetches user data from Spotify API."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None

async def refresh_access_token(user: User, db: AsyncSession):
    """Gets a new access token using the user's refresh token."""

    user_token = user.token
    if not user_token:
        raise Exception("User has no token to refresh!")
    
    # TODO: get refreshed token from Spotify
