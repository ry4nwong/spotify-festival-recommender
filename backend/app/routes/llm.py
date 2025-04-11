from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app.llm import gpt2
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.dependencies import get_db
from app.services.llm_service import perform_hybrid_search
from app.services.auth_service import get_current_user
from app.models.user import User
import numpy as np
import os
import requests
import json

llm_router = APIRouter(prefix="/llm", tags=["LLM"])

@llm_router.post("/generate")
async def generate(prompt: str):
    """Generates a response from GPT-2 LLM."""
    response = await gpt2.generate_text(prompt)
    return {"response": response}

@llm_router.get("/search", response_model=None)
async def hybrid_search(query: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """API wrapper for hybrid similarity search, returns top 5 festivals based on query."""
    return await perform_hybrid_search(query, db)

@llm_router.post("/test-mistral")
async def test_mistral(query: str):
    """Tests Mistral AI from OpenRouter endpoint. Try not to use too many times"""
    api_key = os.getenv('OPENROUTER_API_KEY')

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "mistralai/mistral-small-3.1-24b-instruct:free",
        "messages": [
            {"role": "user", "content": query}
        ]
    }

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code != 200:
        return JSONResponse({"error": response.text}, status_code=response.status_code)

    try:
        content = response.json()
        message = content["choices"][0]["message"]["content"]
        return {"response": message}
    except Exception as e:
        return JSONResponse({"error": "Failed to parse OpenRouter response", "details": str(e)}, status_code=500)