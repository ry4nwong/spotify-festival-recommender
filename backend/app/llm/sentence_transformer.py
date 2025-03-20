from sentence_transformers import SentenceTransformer
import asyncio

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

async def generate_embedding(text):
    return await asyncio.to_thread(model.encode, text)