from typing import List

from database_connection import DatabaseConnection
from dotenv import load_dotenv
import os

if not os.getenv("KUBERNETES_SERVICE_HOST"):
    load_dotenv()
# Initialize database connection
database_connection = DatabaseConnection()
session_status = {}
session_context = {}
session_sources = {}
session_logs = {}

async def update_status(user_id: str, status: str):
    """Update the status for a specific session."""
    session_status[user_id] = status

async def get_status(uid: str) -> str:
    """Get the status for a specific session."""
    return session_status.get(uid, "Status not found...")

async def update_context(user_id: str, context: str):
    """Update the context for a specific session."""
    session_context[user_id] = context

async def get_context(uid: str) -> str:
    """Get the context for a specific session."""
    return session_context.get(uid, "Context not found...")

async def update_sources(user_id: str, sources: List[str]):
    """Update the sources for a specific session."""
    session_sources[user_id] = sources

async def get_sources(uid: str) -> List[str]:
    """Get the sources for a specific session."""
    return session_sources.get(uid, [])

async def update_logs(user_id: str, logs: str):
    """Update the logs for a specific session."""
    session_logs[user_id] = session_logs.get(user_id, "") + "\n\n"+ logs

async def get_logs(uid: str) -> str:
    """Get the logs for a specific session."""
    return session_logs.get(uid, "")

async def reset_logs(uid: str) -> None:
    session_logs[uid] = ""



