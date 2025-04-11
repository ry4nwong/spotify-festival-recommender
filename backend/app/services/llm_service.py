from app.llm import sentence_transformer
from app.models.embedding import Embedding
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.llm.langchain import text_splitter
from rapidfuzz import fuzz
import numpy as np
from sqlalchemy import text

async def generate_embeddings(festivals: list, db: AsyncSession):
    """Generates embeddings for a list of festivals."""
    chunk_metadata = []

    # generate chunks from festival descriptors
    for festival in festivals:
        artist_list = ", ".join(festival.artists) if festival.artists else "various artists"
        tag_list = ", ".join(festival.tags)

        festival_text = (
            f"Name: {festival.name} "
            f"Location: {festival.location} "
            f"Dates: {festival.date} "
            f"Description: {festival.description} "
            f"Frequently asked questions: {festival.faq} "
            f"Featured artists: {artist_list}. "
            f"Featured tags: {tag_list}."
        )
        chunks = text_splitter.split_text(festival_text)
        for i, chunk in enumerate(chunks):
            chunk_metadata.append((festival, i, chunk))

    # deduplicate chunks, can sometimes have duplicates
    seen = set()
    unique_chunks = []
    for metadata in chunk_metadata:
        key = (metadata[0].name, metadata[1])
        if key not in seen:
            seen.add(key)
            unique_chunks.append(metadata)
    
    # delete old embeddings before insertion
    for festival, _, _ in unique_chunks:
        await db.execute(delete(Embedding).where(Embedding.name == festival.name))

    chunk_texts = [chunk[2] for chunk in unique_chunks]
    embeddings = await sentence_transformer.generate_embeddings(chunk_texts)

    for (festival, index, text), embedding in zip(unique_chunks, embeddings):
        new_embedding = Embedding(name=festival.name, chunk_index=index, text=text, embedding=embedding)
        await db.merge(new_embedding)

    await db.commit()

async def perform_hybrid_search(query: str, db: AsyncSession):
    """Completes a hybrid search (semantic + keyword) and returns top 5 festivals based on the input."""
    # generate embedding
    embedding = await sentence_transformer.generate_embedding(query)
    norm = np.linalg.norm(embedding)
    normalized_embedding = embedding if norm == 0 else embedding / norm
    vector_str = "[" + ", ".join(str(x) for x in normalized_embedding) + "]"

    # get top 50 most similar chunks with semantic search
    sql = text("""
        SELECT name, text, embedding <-> :embedding AS distance
        FROM embeddings
        ORDER BY embedding <-> :embedding
        LIMIT 50
    """)
    result = await db.execute(sql, {"embedding": vector_str})
    rows = result.fetchall()

    # calculate hybrid score with keyword matching
    scored_results = []
    for row in rows:
        semantic_score = 1.0 - row.distance
        keyword_score = fuzz.partial_ratio(query.lower(), row.text.lower()) / 100.0

        hybrid_score = 0.6 * semantic_score + 0.4 * keyword_score
        scored_results.append({
            "name": row.name,
            "text": row.text,
            "semantic_score": semantic_score,
            "keyword_score": keyword_score,
            "hybrid_score": hybrid_score
        })

    # get top 5 unique festivals
    unique_festivals = {}
    for result in scored_results:
        name = result["name"]
        if name not in unique_festivals or result["hybrid_score"] > unique_festivals[name]["hybrid_score"]:
            unique_festivals[name] = result

    top_k = sorted(unique_festivals.values(), key=lambda x: x["hybrid_score"], reverse=True)[:5]

    return top_k