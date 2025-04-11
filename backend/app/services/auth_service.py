from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from app.models.user import User
from app.models.auth_token import AuthToken
from app.services.spotify_service import get_user_data
from app.database.dependencies import get_db
import requests
import jwt
import os

async def store_user_token(token_info: dict, db: AsyncSession):
    """Finds the existing user and updates token information upon login, or creates a new user if not found."""

    user_data = await get_user_data(token_info['access_token'])
    if not user_data:
        raise Exception("Failed to fetch user data from Spotify!")
    
    print(user_data)

    # Check db for existing user
    user = await db.execute(select(User).options(selectinload(User.token)).where(User.user_id == user_data['id']))
    user = user.scalars().first()
    if not user:
        user = User(
            user_id=user_data['id'],
            display_name=user_data['display_name'],
            first_name="Temp",
            last_name="Temp",
            profile_picture=user_data['images'][0]['url'] if user_data['images'] else None
        )
    else:
        # Update user info if needed
        user.display_name = user_data['display_name']
        user.profile_picture = user_data['images'][0]['url'] if user_data['images'] else None

    # Update user token information
    if user.token:
        user.token.access_token = token_info['access_token']
        user.token.refresh_token = token_info['refresh_token']
        user.token.expires_at = datetime.fromtimestamp(token_info['expires_at'])
    else:
        user.token = AuthToken(
            user_id=user_data['id'],
            access_token=token_info['access_token'],
            refresh_token=token_info['refresh_token'],
            expires_at=datetime.fromtimestamp(token_info['expires_at'])
        )

    db.add(user)
    await db.commit()
    return await issue_jwt(user)

async def issue_jwt(user: User):
    """Issues a JWT token for the user."""
    now = datetime.now()
    expire_time = now + timedelta(minutes=60) # Token valid for 60 minutes

    payload = {
        "sub": user.user_id,
        "iat": now,
        "exp": expire_time
    }

    return jwt.encode(payload, os.getenv("JWT_SECRET_KEY"), algorithm=os.getenv("JWT_ALGORITHM"))

security = HTTPBearer()

async def get_current_user(db: AsyncSession = Depends(get_db), credentials: HTTPAuthorizationCredentials = Security(security)):
    """Decodes a given JWT token for authentication."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=[os.getenv("JWT_ALGORITHM")])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid JWT payload")
    except jwt.ExpiredSignatureError:
        # TODO: Token has expired, log out the user
        return None
    except jwt.InvalidTokenError:
        # TODO: Invalid token, log out the user (?)
        return None
    
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user