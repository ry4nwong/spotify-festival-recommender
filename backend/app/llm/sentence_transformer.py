from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import asyncio
import numpy as np

tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-mpnet-base-v2')
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

async def generate_embedding(festival_text: str):
    """Gives a NORMALIZED vector embedding based on a single festival descriptor."""
    embedding = await asyncio.to_thread(model.encode, festival_text)
    norm = np.linalg.norm(embedding)
    return embedding if norm == 0 else embedding / norm

async def generate_embeddings(festival_texts: list):
    """Gives a NORMALIZED vector embedding based on multiple festival descriptors."""
    embeddings = await asyncio.to_thread(model.encode, festival_texts, truncation=True, max_length=512)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return embeddings / norms