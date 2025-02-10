from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import RedirectResponse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from dotenv import load_dotenv
import os

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

# Initialize Spotify OAuth with configuration
def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope="user-library-read playlist-modify-private"
    )

# Gain Spotify access token
@auth_router.get("/login", response_class=RedirectResponse)
async def login(sp_oauth: SpotifyOAuth = Depends(get_spotify_oauth)):
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(url=auth_url)

# Callback from Spotify login
@auth_router.get("/callback")
async def callback(code: str = Query(...), sp_oauth: SpotifyOAuth = Depends(get_spotify_oauth)):
    try:
        token_info = sp_oauth.get_access_token(code)
        return {"message": "Login successful!", "token_info": token_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))