from app.llm import sentence_transformer
from app.models.embedding import Embedding
from sqlalchemy.ext.asyncio import AsyncSession

async def generate_embeddings(festivals: list, db: AsyncSession):
    """Generates embeddings for a list of festivals."""
    chunk_metadata = []

    for festival in festivals:
        artist_list = ", ".join(festival.artists) if festival.artists else "various artists"
        tag_list = ", ".join(festival.tags)

        chunks = sentence_transformer.chunk_text(
            f"{festival.name} is a festival in {festival.location} on {festival.date}. "
            f"Featured artists include: {artist_list}. "
            f"Featured tags include: {tag_list}."
        )
        for i, chunk in enumerate(chunks):
            chunk_metadata.append((festival, i, chunk))

    seen = set()
    unique_chunks = []
    for metadata in chunk_metadata:
        key = (metadata[0], metadata[1])
        if key not in seen:
            seen.add(key)
            unique_chunks.append(metadata)
    
    chunk_texts = [chunk[2] for chunk in unique_chunks]

    embeddings = await sentence_transformer.generate_embeddings(chunk_texts)

    for (festival, index, text), embedding in zip(unique_chunks, embeddings):
        new_embedding = Embedding(name=festival.name, chunk_index=index, text=text, embedding=embedding)
        await db.merge(new_embedding)

    await db.commit()

