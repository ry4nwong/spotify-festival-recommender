from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import RedirectResponse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from dotenv import load_dotenv
import os

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

def get_spotify_oauth():
    """Initializes Spotify OAUTH with configuration."""
    return SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope="user-library-read playlist-modify-private"
    )

@auth_router.get("/login", response_class=RedirectResponse)
async def login(sp_oauth: SpotifyOAuth = Depends(get_spotify_oauth)):
    """Gathers Spotify access token to be used as login."""
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(url=auth_url)

@auth_router.get("/callback")
async def callback(code: str = Query(...), sp_oauth: SpotifyOAuth = Depends(get_spotify_oauth)):
    """Callback functionality from Spotify login."""
    try:
        token_info = sp_oauth.get_access_token(code)
        return {"message": "Login successful!", "token_info": token_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))