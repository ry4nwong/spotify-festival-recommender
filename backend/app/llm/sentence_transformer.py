from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import asyncio

tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-mpnet-base-v2')
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

def chunk_text(text, max_tokens=512, stride=128):
    """Chunks a given text by length max_tokens for embedding generation."""
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = []
    for i in range(0, len(tokens), max_tokens - stride):
        chunk_tokens = tokens[i : i + max_tokens]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
    
    return chunks

async def generate_embedding(festival_text: str):
    """Gives a vector embedding based on multiple festival descriptors."""
    return await asyncio.to_thread(model.encode, festival_text)

async def generate_embeddings(festival_texts: list):
    """Gives a vector embedding based on multiple festival descriptors."""
    return await asyncio.to_thread(model.encode, festival_texts)