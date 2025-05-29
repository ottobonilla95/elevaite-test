import asyncio
from database_connection import DatabaseConnection
from dotenv import load_dotenv
load_dotenv()
# Initialize database connection
database_connection = DatabaseConnection()
session_status = {}

async def update_status(user_if: str, status: str):
    """Update the status for a specific session."""
    session_status[user_if] = status

async def get_status(uid: str) -> str:
    """Get the status for a specific session."""
    return session_status.get(uid, "Status not found...")




