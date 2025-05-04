import asyncio

session_status = {}

async def update_status(user_if: str, status: str):
    """Update the status for a specific session."""
    session_status[user_if] = status

async def get_status(uid: str) -> str:
    """Get the status for a specific session."""
    return session_status.get(uid, "Status not found...")




