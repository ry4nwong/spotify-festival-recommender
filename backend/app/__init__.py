from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.database.db_init import init_db
from app.routes.auth import auth_router
from app.routes.db import db_router
from app.routes.data import data_router
from app.routes.llm import llm_router

load_dotenv()

app = FastAPI(title="AI Festival Recommender API")

# Routes
app.include_router(llm_router)
app.include_router(auth_router)
app.include_router(data_router)
app.include_router(db_router)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    print("App shut down")