from transformers import pipeline
import asyncio

generator = pipeline("text-generation", model="gpt2")

async def generate_text(prompt: str, max_length: int = 100):
    return await asyncio.to_thread(generator, prompt, max_length=max_length)