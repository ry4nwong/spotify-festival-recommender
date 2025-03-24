from fastapi import APIRouter, Depends
from app.llm import gpt2, sentence_transformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.embedding import Embedding
from app.database.dependencies import get_db

llm_router = APIRouter(prefix="/llm", tags=["LLM"])

@llm_router.post("/generate")
async def generate(prompt: str):
    """Generates a response from GPT-2 LLM."""
    response = await gpt2.generate_text(prompt)
    return {"response": response}

@llm_router.get("/search")
async def semantic_search(query: str, db: AsyncSession = Depends(get_db)):
    """Completes a semantic search and returns top 3 festivals based on the input."""
    embedding = await sentence_transformer.generate_embedding(query)
    embedding_list = embedding.tolist()

    statement = (
        select(Embedding)
        .order_by(Embedding.embedding.cosine_distance(embedding_list))
        .limit(3)
    )

    result = await db.execute(statement)
    rows = result.scalars().all()

    return [
        {
            "name": row.name,
            "text": row.text
        }
        for row in rows
    ]