from fastapi import APIRouter, Depends
from app.llm.gpt2 import generate_text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.dependencies import get_db

llm_router = APIRouter(prefix="/llm", tags=["LLM"])

@llm_router.post("/generate")
async def generate(prompt: str):
    response = await generate_text(prompt)
    return {"response": response}