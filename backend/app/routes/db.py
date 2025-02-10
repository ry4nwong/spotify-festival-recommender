from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.future import select
from app.database.dependencies import get_db
from app.models.festival import Festival

db_router = APIRouter(prefix="/db", tags=["Database"])

@db_router.get("/festivals")
async def get_current_festivals(db: AsyncSession = Depends(get_db)):
    return await query("festivals", db)

@db_router.get("/artists")
async def get_current_artists(db: AsyncSession = Depends(get_db)):
    return await query("artists", db)

@db_router.get("/tags")
async def get_current_tags(db: AsyncSession = Depends(get_db)):
    return await query("tags", db)

# Helper function to get existing tables in database
# LEAVE HERE FOR NOW, SHOULD BE IN FESTIVAL_SERVICE
async def query(table: str, db: AsyncSession):
    try:
        sql_query = text(f"SELECT * FROM {table}")
        result = await db.execute(sql_query)
        rows = [dict(row) for row in result.mappings()]
        return rows
    except Exception as e:
        return {"error": f"Error executing query: {table}. Details: {str(e)}"}