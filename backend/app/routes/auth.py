from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from app.database.dependencies import get_db
from app.services.auth_service import store_user_token
from app.services.spotify_service import get_spotify_oauth
import os

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.get("/login", response_class=RedirectResponse)
async def login(sp_oauth: SpotifyOAuth = Depends(get_spotify_oauth)):
    """Gathers Spotify access token to be used as login."""
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(url=auth_url)

@auth_router.get("/callback")
async def callback(code: str = Query(...), sp_oauth: SpotifyOAuth = Depends(get_spotify_oauth), db: AsyncSession = Depends(get_db)):
    """Callback functionality from Spotify login."""
    try:
        token_info = sp_oauth.get_access_token(code)
        return await store_user_token(token_info, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))